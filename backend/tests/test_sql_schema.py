import os
import re
import pytest

def test_sql_migration_files_exist():
    migration_file = os.path.join(os.path.dirname(__file__), "..", "..", "db", "migrations", "001_initial_schema.sql")
    seed_file = os.path.join(os.path.dirname(__file__), "..", "..", "db", "seed", "001_synthetic_seed.sql")
    
    assert os.path.exists(migration_file), "Migration SQL file must exist"
    assert os.path.exists(seed_file), "Seed SQL file must exist"

    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    with open(seed_file, "r", encoding="utf-8") as f:
        seed_sql = f.read()

    # Verify all 14 required tables are present in migration
    required_tables = [
        "users", "dealers", "customers", "cases", "invoices",
        "invoice_line_items", "installation_images", "product_price_benchmarks",
        "registered_assets", "risk_signals", "risk_scores", "entity_relationships",
        "verification_tasks", "audit_log"
    ]
    
    for table in required_tables:
        pattern = rf"CREATE TABLE IF NOT EXISTS {table}\s*\("
        assert re.search(pattern, migration_sql, re.IGNORECASE), f"Missing CREATE TABLE for {table}"

    # Verify seed data contains minimums
    # 3 dealers
    assert "Apex Solar Equipment Pvt Ltd" in seed_sql
    assert "SunPower Retail & Infra Solutions" in seed_sql
    assert "Radiant AgroTech Distributions" in seed_sql

    # Verify 10 cases
    case_matches = re.findall(r"CAS-2026-\d{3}", seed_sql)
    assert len(case_matches) >= 10, f"Found {len(case_matches)} synthetic cases, expected >= 10"

    # Verify price benchmarks
    benchmark_matches = re.findall(r"44444444-4444-4444-4444-4444444444\d{2}", seed_sql)
    assert len(benchmark_matches) >= 5, "Expected at least 5 price benchmarks"

    # Verify registered assets
    reg_matches = re.findall(r"66666666-6666-6666-6666-6666666666\d{2}", seed_sql)
    assert len(reg_matches) >= 5, "Expected at least 5 registered assets"
