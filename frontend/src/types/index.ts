export type RiskLevel = 'low' | 'medium' | 'high' | 'critical' | 'requires_verification' | 'unknown';

export type CaseStatus = 'submitted' | 'verification_pending' | 'under_review' | 'flagged' | 'verified' | 'rejected';

export type DealerStatus = 'active' | 'under_review' | 'flagged' | 'suspended';

export type CheckStatus = 'PASS' | 'ANOMALY' | 'INCONCLUSIVE' | 'NOT_CHECKED';

export type CheckSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH';

export interface VerificationCheckItem {
  check_type: string;
  check_name: string;
  status: CheckStatus;
  severity: CheckSeverity;
  message: string;
  evidence: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface InvoiceVerificationSummary {
  invoice_id: string;
  case_id: string;
  extraction_status: string;
  verification_status: string;
  total_checks: number;
  passed_count: number;
  anomaly_count: number;
  inconclusive_count: number;
  checks: VerificationCheckItem[];
  signals_generated: Record<string, any>[];
  verified_at: string;
  notes: string;
}

export interface EmbeddingMatchItem {
  candidate_image_id: string;
  candidate_case_id: string;
  similarity: number;
  threshold: number;
  is_above_threshold: boolean;
  match_type: 'cross_case' | 'same_case';
  model: string;
  model_version: string;
  dimension: number;
  created_at?: string;
}

export interface EmbeddingVerificationSummary {
  image_id: string;
  case_id: string;
  model: string;
  model_version: string;
  embedding_dimension: number;
  has_embedding: boolean;
  status: CheckStatus;
  top_similarity: number;
  threshold: number;
  top_matches: EmbeddingMatchItem[];
  check_item?: VerificationCheckItem;
  verified_at: string;
  notes?: string;
}

export interface ImageVerificationSummary {
  image_id: string;
  case_id: string;
  original_filename: string;
  image_type: string;
  verification_status: string;
  total_checks: number;
  passed_count: number;
  anomaly_count: number;
  inconclusive_count: number;
  checks: VerificationCheckItem[];
  signals_generated: Record<string, any>[];
  exif_summary: {
    has_exif?: boolean;
    camera_make?: string;
    camera_model?: string;
    capture_timestamp?: string;
    gps_lat?: number;
    gps_lng?: number;
  };
  phash?: string;
  embedding_summary?: EmbeddingVerificationSummary;
  verified_at: string;
  notes: string;
}

export interface InstallationImage {
  id: string;
  case_id: string;
  image_type: string;
  file_path: string;
  original_filename: string;
  file_size_bytes?: number;
  mime_type?: string;
  phash?: string;
  exif_timestamp?: string;
  exif_lat?: number;
  exif_lng?: number;
  exif_device_model?: string;
  verification_status: string;
  signed_url?: string;
  created_at: string;
}

export interface Dealer {
  id: string;
  dealer_code: string;
  name: string;
  business_name: string;
  gstin?: string;
  pan?: string;
  cin?: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  contact_email: string;
  contact_phone: string;
  status: DealerStatus;
  risk_tier: 'low' | 'medium' | 'high' | 'critical';
  total_cases: number;
  flagged_cases: number;
  created_at: string;
}

export interface Customer {
  id: string;
  customer_code: string;
  full_name: string;
  contact_phone: string;
  contact_email?: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
}

export interface Case {
  id: string;
  case_number: string;
  dealer_id: string;
  customer_id: string;
  dealer_name?: string;
  customer_name?: string;
  asset_type: string;
  claimed_installation_address: string;
  loan_amount: number;
  status: CaseStatus;
  risk_level: RiskLevel;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface RiskSignal {
  id: string;
  case_id: string;
  category: 'price' | 'image' | 'geo' | 'dealer_network' | 'serial_asset' | 'document';
  signal_name: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence_score: number;
  evidence_payload: Record<string, any>;
  description: string;
  created_at: string;
}

export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH';

export interface ScoreComponentItem {
  signal_id?: string;
  signal_type: string;
  group: string;
  source: string;
  severity: string;
  policy_weight: number;
  effective_contribution: number;
  is_group_capped: boolean;
  group_cap_applied?: number;
  description: string;
  evidence: Record<string, any>;
  created_at?: string;
}

export interface GroupContributionSummary {
  group: string;
  raw_sum: number;
  group_cap: number;
  effective_contribution: number;
  signal_count: number;
}

export interface RiskScore {
  id: string;
  case_id: string;
  overall_score: number; // 0 - 100
  raw_score?: number;
  risk_level: RiskLevel;
  risk_band?: RiskBand;
  policy_version?: string;
  recommended_action?: string;
  price_anomaly_score: number;
  image_anomaly_score: number;
  dealer_network_score: number;
  serial_anomaly_score: number;
  components?: ScoreComponentItem[];
  group_contributions?: Record<string, GroupContributionSummary>;
  summary_reasoning: string;
  calculated_at: string;
  audit_note?: string;
}

export type RiskAssessmentResult = RiskScore;

export interface EvidenceItem {
  id: string;
  case_id: string;
  type: 'invoice' | 'image' | 'geo' | 'serial_check' | 'dealer_audit';
  title: string;
  status: 'verified' | 'suspicious' | 'pending' | 'inconclusive';
  details: string;
  file_url?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface VerificationTask {
  id: string;
  case_id: string;
  task_type: 'physical_site_visit' | 'oem_serial_check' | 'telephonic_verification' | 'gst_cross_check' | 'document_reupload';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  assigned_to?: string;
  instructions?: string;
  findings?: string;
  created_at: string;
  completed_at?: string;
}

export type RelationshipCategory = 'structural' | 'evidence' | 'potential_anomaly';

export interface RelationshipItem {
  id: string;
  case_id?: string;
  source_entity_type: string;
  source_entity_id: string;
  target_entity_type: string;
  target_entity_id: string;
  relationship_type: string;
  category: RelationshipCategory;
  description: string;
  strength: number;
  risk_weight: number;
  policy_version: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  entity_type: string;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  category: RelationshipCategory;
  strength: number;
  label: string;
  metadata?: Record<string, any>;
}

export interface RelationshipGraphResponse {
  case_id?: string;
  dealer_id?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: Record<string, number>;
}

export interface DealerConcentrationSummary {
  dealer_id: string;
  dealer_name: string;
  dealer_code: string;
  total_cases: number;
  distinct_customers: number;
  total_invoices: number;
  registered_assets: number;
  structural_relationships_count: number;
  evidence_relationships_count: number;
  potential_anomalies_count: number;
  shared_attribute_clusters: {
    attribute_type: string;
    affected_entities_count: number;
    masked_reference?: string;
  }[];
  active_verification_anomalies_count: number;
  policy_note: string;
}

export interface CaseRelationshipAnalysisResponse {
  case_id: string;
  dealer_id: string;
  customer_id: string;
  policy_version: string;
  structural_relationships: RelationshipItem[];
  evidence_relationships: RelationshipItem[];
  potential_anomalies: RelationshipItem[];
  relationship_signals: Record<string, any>[];
  total_relationships_count: number;
  graph: RelationshipGraphResponse;
  evaluated_at: string;
  policy_note: string;
}

export type PipelineRunStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'PARTIAL' | 'FAILED';

export type PipelineStageName = 
  | 'INVOICE_EXTRACTION'
  | 'INVOICE_VERIFICATION'
  | 'IMAGE_PROCESSING'
  | 'RELATIONSHIP_ANALYSIS'
  | 'RISK_CALCULATION'
  | 'VERIFICATION_TASK_DISPATCH';

export type StageStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'SKIPPED' | 'INCONCLUSIVE' | 'FAILED';

export interface PipelineStageItem {
  id: string;
  stage_name: PipelineStageName;
  status: StageStatus;
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  result_summary: Record<string, any>;
  error_code?: string;
  error_message?: string;
}

export interface PipelineStatusResponse {
  case_id: string;
  run_id?: string;
  status: PipelineRunStatus;
  current_stage?: string;
  pipeline_version: string;
  stages: PipelineStageItem[];
  risk_score?: number;
  risk_band?: string;
  recommended_action?: string;
  verification_task_id?: string;
  started_at?: string;
  completed_at?: string;
  total_duration_ms: number;
  message: string;
}

// Phase 9: Workflow Automation & Alerts
export type WorkflowEventType = 
  | 'CASE_VERIFICATION_COMPLETED'
  | 'CASE_VERIFICATION_HIGH_RISK'
  | 'VERIFICATION_TASK_CREATED'
  | 'CASE_VERIFICATION_PARTIAL'
  | 'CASE_VERIFICATION_FAILED';

export type WorkflowEventStatus = 'PENDING' | 'PROCESSING' | 'DELIVERED' | 'FAILED' | 'RETRY_PENDING';

export interface WorkflowEventPayload {
  event_id: string;
  event_type: WorkflowEventType;
  event_version: string;
  case_id: string;
  case_number: string;
  pipeline_run_id?: string;
  risk_score: number;
  risk_band: string;
  recommended_action: string;
  top_anomalies: string[];
  verification_task_id?: string;
  case_url: string;
  timestamp: string;
}

export interface WorkflowEventRecord {
  id: string;
  event_id: string;
  event_type: WorkflowEventType;
  event_version: string;
  case_id: string;
  pipeline_run_id?: string;
  payload: WorkflowEventPayload;
  status: WorkflowEventStatus;
  attempt_count: number;
  max_attempts: number;
  next_attempt_at?: string;
  locked_at?: string;
  locked_by?: string;
  last_attempt_at?: string;
  last_error?: string;
  processed_at?: string;
  created_at: string;
}

export interface WorkflowEventListResponse {
  case_id: string;
  events: WorkflowEventRecord[];
  total_count: number;
}


