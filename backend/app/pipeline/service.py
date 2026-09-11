import uuid
import logging
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.pipeline.models import (
    PipelineRunStatusEnum,
    PipelineStageEnum,
    StageStatusEnum,
    PipelineStageItem,
    PipelineRunRecord,
    PipelineStatusResponse
)
from app.pipeline.executor import pipeline_executor
from app.db.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)

# In-memory storage for active runs and history (synced with DB when available)
_ACTIVE_RUNS_LOCK = threading.Lock()
_ACTIVE_CASE_RUNS: Dict[str, str] = {}  # case_id -> run_id
_PIPELINE_RUNS_HISTORY: Dict[str, List[PipelineRunRecord]] = {}


class ActivePipelineRunConflictException(Exception):
    """Raised when an active pipeline run already exists for the case."""
    def __init__(self, case_id: str, active_run_id: str):
        self.case_id = case_id
        self.active_run_id = active_run_id
        super().__init__(f"Active verification pipeline run '{active_run_id}' already in progress for case '{case_id}'.")


class PipelineService:
    """
    Service managing pipeline run lifecycles, database-enforced concurrency locks,
    idempotent execution, and run history.
    """

    def start_pipeline_run(
        self,
        case_id: str,
        policy_version: str = "risk-v1",
        force_rerun: bool = False
    ) -> PipelineStatusResponse:
        """
        Initializes and executes a case verification pipeline run with strict concurrency protection.
        """
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 1. Database & In-Memory Concurrency Guard
        with _ACTIVE_RUNS_LOCK:
            existing_active = _ACTIVE_CASE_RUNS.get(case_id)
            if existing_active and not force_rerun:
                raise ActivePipelineRunConflictException(case_id, existing_active)

            admin_client = get_supabase_admin_client()
            if admin_client and not force_rerun:
                try:
                    # Attempt to check DB for active runs
                    res = admin_client.table("verification_pipeline_runs").select("id").eq("case_id", case_id).in_("status", ["QUEUED", "PROCESSING"]).execute()
                    if res and res.data:
                        active_db_id = res.data[0]["id"]
                        _ACTIVE_CASE_RUNS[case_id] = active_db_id
                        raise ActivePipelineRunConflictException(case_id, active_db_id)
                except ActivePipelineRunConflictException:
                    raise
                except Exception as e:
                    logger.debug(f"DB check note: {e}")

            # Register active lock
            _ACTIVE_CASE_RUNS[case_id] = run_id

        # 2. Insert initial run record (enforcing DB unique partial index)
        initial_record = PipelineRunRecord(
            id=run_id,
            case_id=case_id,
            status=PipelineRunStatusEnum.PROCESSING,
            current_stage="INVOICE_EXTRACTION",
            pipeline_version="pipeline-v1",
            started_at=now,
            created_at=now,
            updated_at=now
        )

        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                admin_client.table("verification_pipeline_runs").insert({
                    "id": run_id,
                    "case_id": case_id,
                    "status": "PROCESSING",
                    "current_stage": "INVOICE_EXTRACTION",
                    "pipeline_version": "pipeline-v1",
                    "started_at": now.isoformat()
                }).execute()
            except Exception as e:
                # If unique constraint violation occurs in DB
                with _ACTIVE_RUNS_LOCK:
                    _ACTIVE_CASE_RUNS.pop(case_id, None)
                if "idx_active_pipeline_run_per_case" in str(e) or "unique" in str(e).lower():
                    raise ActivePipelineRunConflictException(case_id, "DB_ACTIVE_LOCK")
                logger.debug(f"DB run insert note: {e}")

        # 3. Retrieve Case Data Context
        case_data = self._get_case_data(case_id)

        try:
            # 4. Execute Stages Sequentially
            final_record = pipeline_executor.execute_pipeline_run(
                run_record=initial_record,
                case_data=case_data,
                policy_version=policy_version
            )

            # 5. Persist Stage Records and Update DB
            self._persist_run_and_stages(final_record)

            # 6. Save in memory history
            if case_id not in _PIPELINE_RUNS_HISTORY:
                _PIPELINE_RUNS_HISTORY[case_id] = []
            _PIPELINE_RUNS_HISTORY[case_id].append(final_record)

            # 7. Phase 9: Record workflow event into outbox and dispatch (Fault-isolated)
            try:
                status_resp = self._build_status_response(final_record)
                top_anoms = []
                for s in final_record.stages:
                    if s.stage_name == PipelineStageEnum.RISK_CALCULATION and s.result_summary:
                        top_anoms = s.result_summary.get("top_anomalies", [])
                        break

                from app.workflow.service import workflow_service
                from app.workflow.dispatcher import outbox_dispatcher

                workflow_service.record_and_enqueue_event(
                    case_id=case_id,
                    case_number=case_data.get("case_number", case_id),
                    risk_score=status_resp.risk_score or 0,
                    risk_band=status_resp.risk_band or "LOW",
                    recommended_action=status_resp.recommended_action or "No immediate additional verification indicated by the configured DIAVN rules.",
                    pipeline_run_id=final_record.id,
                    top_anomalies=top_anoms,
                    verification_task_id=status_resp.verification_task_id
                )
                # Attempt non-blocking outbox dispatch
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(outbox_dispatcher.dispatch_next_event())
                except RuntimeError:
                    pass
            except Exception as e:
                logger.debug(f"Phase 9 workflow event outbox emission note: {e}")

            return self._build_status_response(final_record)

        finally:
            # Release concurrency lock
            with _ACTIVE_RUNS_LOCK:
                _ACTIVE_CASE_RUNS.pop(case_id, None)

    def get_case_pipeline_status(self, case_id: str) -> PipelineStatusResponse:
        """
        Retrieves the latest pipeline run status for the case.
        """
        # 1. Check in-memory history
        runs = _PIPELINE_RUNS_HISTORY.get(case_id, [])
        if runs:
            latest = runs[-1]
            return self._build_status_response(latest)

        # 2. Check Supabase
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("verification_pipeline_runs").select("*").eq("case_id", case_id).order("created_at", desc=True).limit(1).execute()
                if res and res.data:
                    run_dict = res.data[0]
                    # Fetch stages
                    stages_res = admin_client.table("verification_pipeline_stages").select("*").eq("pipeline_run_id", run_dict["id"]).execute()
                    stages = []
                    if stages_res and stages_res.data:
                        for s in stages_res.data:
                            stages.append(PipelineStageItem(
                                id=s["id"],
                                stage_name=s["stage_name"],
                                status=s["status"],
                                started_at=datetime.fromisoformat(s["started_at"]) if s.get("started_at") else None,
                                completed_at=datetime.fromisoformat(s["completed_at"]) if s.get("completed_at") else None,
                                duration_ms=s.get("duration_ms", 0),
                                result_summary=s.get("result_summary", {})
                            ))
                    record = PipelineRunRecord(
                        id=run_dict["id"],
                        case_id=case_id,
                        status=run_dict["status"],
                        current_stage=run_dict.get("current_stage"),
                        stages=stages,
                        started_at=datetime.fromisoformat(run_dict["started_at"]) if run_dict.get("started_at") else datetime.now(timezone.utc),
                        completed_at=datetime.fromisoformat(run_dict["completed_at"]) if run_dict.get("completed_at") else None,
                        total_duration_ms=run_dict.get("total_duration_ms", 0)
                    )
                    return self._build_status_response(record)
            except Exception as e:
                logger.debug(f"Could not load status from Supabase: {e}")

        # 3. If never run before, return clean idle response
        return PipelineStatusResponse(
            case_id=case_id,
            status=PipelineRunStatusEnum.QUEUED,
            current_stage=None,
            message="No pipeline runs have been executed for this case yet."
        )

    def get_case_pipeline_runs(self, case_id: str) -> List[PipelineRunRecord]:
        """
        Returns full auditable pipeline run history for the case.
        """
        return _PIPELINE_RUNS_HISTORY.get(case_id, [])

    def _persist_run_and_stages(self, run_record: PipelineRunRecord):
        """
        Persists completed pipeline run and stage execution records to database.
        """
        admin_client = get_supabase_admin_client()
        if not admin_client:
            return

        try:
            # Update Run
            admin_client.table("verification_pipeline_runs").update({
                "status": run_record.status.value,
                "current_stage": run_record.current_stage,
                "completed_at": run_record.completed_at.isoformat() if run_record.completed_at else None,
                "total_duration_ms": run_record.total_duration_ms,
                "error_code": run_record.error_code,
                "error_message": run_record.error_message,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", run_record.id).execute()

            # Insert Stage Records
            for stage in run_record.stages:
                admin_client.table("verification_pipeline_stages").insert({
                    "id": stage.id,
                    "pipeline_run_id": run_record.id,
                    "case_id": run_record.case_id,
                    "stage_name": stage.stage_name.value,
                    "status": stage.status.value,
                    "started_at": stage.started_at.isoformat() if stage.started_at else None,
                    "completed_at": stage.completed_at.isoformat() if stage.completed_at else None,
                    "duration_ms": stage.duration_ms,
                    "result_summary": stage.result_summary,
                    "error_code": stage.error_code,
                    "error_message": stage.error_message
                }).execute()
        except Exception as e:
            logger.debug(f"Could not sync pipeline execution to DB: {e}")

    def _build_status_response(self, record: PipelineRunRecord) -> PipelineStatusResponse:
        """
        Constructs a structured PipelineStatusResponse with Phase 6 risk engine details.
        """
        risk_score = None
        risk_band = None
        recommended_action = None
        task_id = None

        # Extract risk results from RISK_CALCULATION stage
        for s in record.stages:
            if s.stage_name == PipelineStageEnum.RISK_CALCULATION and s.result_summary:
                risk_score = s.result_summary.get("overall_score")
                risk_band = s.result_summary.get("risk_band")
                recommended_action = s.result_summary.get("recommended_action")
            elif s.stage_name == PipelineStageEnum.VERIFICATION_TASK_DISPATCH and s.result_summary:
                task_id = s.result_summary.get("task_id")

        return PipelineStatusResponse(
            case_id=record.case_id,
            run_id=record.id,
            status=record.status,
            current_stage=record.current_stage,
            pipeline_version=record.pipeline_version,
            stages=record.stages,
            risk_score=risk_score,
            risk_band=risk_band,
            recommended_action=recommended_action,
            verification_task_id=task_id,
            started_at=record.started_at,
            completed_at=record.completed_at,
            total_duration_ms=record.total_duration_ms,
            message=f"Pipeline execution {record.status.value.lower()} ({len(record.stages)} stages recorded)."
        )

    def _get_case_data(self, case_id: str) -> Dict[str, Any]:
        from app.graph.service import relationship_service
        return relationship_service.get_case_data(case_id)


pipeline_service = PipelineService()
