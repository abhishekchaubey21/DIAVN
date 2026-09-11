import logging
from typing import List, Dict, Any, Optional
from app.verification.models import CheckTypeEnum, CheckStatusEnum, CheckSeverityEnum, VerificationCheckItem
from app.verification.normalization import normalize_product_name

logger = logging.getLogger(__name__)

# In-memory benchmark registry matching database table 'product_price_benchmarks'
# Can query Supabase/Postgres when available or use this authoritative reference
PRODUCT_PRICE_BENCHMARKS = [
    {
        "id": "44444444-4444-4444-4444-444444444401",
        "asset_category": "Solar Inverter",
        "brand": "SunGuard",
        "model_name": "SG-5KVA-HYBRID",
        "keywords": ["solar inverter", "5kva", "sunguard", "hybrid inverter", "inverter 5kva"],
        "benchmark_avg_price": 52000.0,
        "benchmark_min_price": 45000.0,
        "benchmark_max_price": 58000.0,
        "default_tolerance_pct": 15.0
    },
    {
        "id": "44444444-4444-4444-4444-444444444402",
        "asset_category": "Solar Water Pump",
        "brand": "AquaSun",
        "model_name": "ASP-5HP-SUB-V4",
        "keywords": ["solar water pump", "solar pump", "5hp", "aquasun", "submersible pump"],
        "benchmark_avg_price": 185000.0,
        "benchmark_min_price": 160000.0,
        "benchmark_max_price": 210000.0,
        "default_tolerance_pct": 15.0
    },
    {
        "id": "44444444-4444-4444-4444-444444444403",
        "asset_category": "Solar PV Panel",
        "brand": "LumiSolar",
        "model_name": "LS-540W-MONO-PERC",
        "keywords": ["solar pv panel", "solar panel", "540w", "lumisolar", "mono perc", "panel 540w"],
        "benchmark_avg_price": 13200.0,
        "benchmark_min_price": 11500.0,
        "benchmark_max_price": 15000.0,
        "default_tolerance_pct": 15.0
    },
    {
        "id": "44444444-4444-4444-4444-444444444404",
        "asset_category": "Solar Inverter",
        "brand": "VoltMax",
        "model_name": "VM-10KW-COMM",
        "keywords": ["solar inverter 10kw", "10kw", "voltmax", "grid tie 10kw"],
        "benchmark_avg_price": 98000.0,
        "benchmark_min_price": 85000.0,
        "benchmark_max_price": 110000.0,
        "default_tolerance_pct": 15.0
    },
    {
        "id": "44444444-4444-4444-4444-444444444405",
        "asset_category": "Micro-Irrigation Controller",
        "brand": "AgroSense",
        "model_name": "ASC-AUTO-V3",
        "keywords": ["micro-irrigation controller", "irrigation controller", "agrosense", "drip controller"],
        "benchmark_avg_price": 32000.0,
        "benchmark_min_price": 28000.0,
        "benchmark_max_price": 36000.0,
        "default_tolerance_pct": 15.0
    },
    {
        "id": "44444444-4444-4444-4444-444444444406",
        "asset_category": "Energy Storage",
        "brand": "PowerCell",
        "model_name": "PC-LFP-48V-100AH",
        "keywords": ["energy storage", "battery bank", "powercell", "4.8kwh", "lithium iron phosphate"],
        "benchmark_avg_price": 110000.0,
        "benchmark_min_price": 95000.0,
        "benchmark_max_price": 125000.0,
        "default_tolerance_pct": 15.0
    }
]


def find_price_benchmark(product_name: str, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Look up matching benchmark from the benchmarks table using normalized keyword matching.
    """
    combined = f"{normalize_product_name(product_name)} {normalize_product_name(description or '')}".strip()
    if not combined:
        return None

    # Search for keyword matches
    for benchmark in PRODUCT_PRICE_BENCHMARKS:
        for kw in benchmark["keywords"]:
            if kw in combined:
                return benchmark

    return None


def verify_price_benchmark(
    line_items: List[Dict[str, Any]],
    tolerance_pct: float = 15.0
) -> List[VerificationCheckItem]:
    """
    Deterministically evaluates invoice line item unit prices against category price benchmarks.
    """
    results: List[VerificationCheckItem] = []

    if not line_items:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.PRICE_BENCHMARK,
                check_name="Price Benchmark Consistency",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="No line items available to evaluate price benchmarks.",
                evidence={"reason": "empty_line_items"}
            )
        )
        return results

    for idx, item in enumerate(line_items):
        product_name = item.get("product_name") or item.get("item_description") or f"Item #{idx+1}"
        unit_price = item.get("unit_price")

        if unit_price is None or unit_price <= 0:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.PRICE_BENCHMARK,
                    check_name=f"Price Benchmark: {product_name}",
                    status=CheckStatusEnum.INCONCLUSIVE,
                    severity=CheckSeverityEnum.INFO,
                    message=f"Unit price for '{product_name}' is missing or non-positive.",
                    evidence={"product": product_name, "unit_price": unit_price}
                )
            )
            continue

        benchmark = find_price_benchmark(product_name, item.get("description"))

        if not benchmark:
            # Critical requirement: Missing benchmark is INCONCLUSIVE, NEVER an anomaly
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.PRICE_BENCHMARK,
                    check_name=f"Price Benchmark: {product_name}",
                    status=CheckStatusEnum.INCONCLUSIVE,
                    severity=CheckSeverityEnum.INFO,
                    message="No benchmark available for this product.",
                    evidence={
                        "product": product_name,
                        "invoice_unit_price": unit_price,
                        "status": "unbenchmarked_product"
                    }
                )
            )
            continue

        benchmark_avg = benchmark["benchmark_avg_price"]
        effective_tolerance = benchmark.get("default_tolerance_pct", tolerance_pct)
        
        lower_bound = benchmark_avg * (1.0 - effective_tolerance / 100.0)
        upper_bound = benchmark_avg * (1.0 + effective_tolerance / 100.0)
        variance_pct = ((unit_price - benchmark_avg) / benchmark_avg) * 100.0

        evidence_payload = {
            "product": product_name,
            "matched_benchmark_model": benchmark["model_name"],
            "invoice_unit_price": unit_price,
            "benchmark_avg_price": benchmark_avg,
            "tolerance_pct": effective_tolerance,
            "allowed_range": [round(lower_bound, 2), round(upper_bound, 2)],
            "variance_pct": round(variance_pct, 2)
        }

        if lower_bound <= unit_price <= upper_bound:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.PRICE_BENCHMARK,
                    check_name=f"Price Benchmark: {product_name}",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message=f"Unit price (₹{unit_price:,.2f}) is within normal benchmark range (₹{lower_bound:,.2f} – ₹{upper_bound:,.2f}).",
                    evidence=evidence_payload
                )
            )
        else:
            severity = CheckSeverityEnum.HIGH if variance_pct > 50.0 else CheckSeverityEnum.MEDIUM
            direction = "above upper bound" if unit_price > upper_bound else "below lower bound"
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.PRICE_BENCHMARK,
                    check_name=f"Price Benchmark: {product_name}",
                    status=CheckStatusEnum.ANOMALY,
                    severity=severity,
                    message=f"Unit price (₹{unit_price:,.2f}) is {direction} of benchmark range (₹{lower_bound:,.2f} – ₹{upper_bound:,.2f}, variance: {variance_pct:+.1f}%).",
                    evidence=evidence_payload
                )
            )

    return results
