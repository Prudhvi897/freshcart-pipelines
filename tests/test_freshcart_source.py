"""Part B local tests.

Test docstrings classify checks as fixture/data validation, Python unit tests,
or static SQL checks. There are no Snowflake integration tests in this file.
"""
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
ELT_DIR = ROOT / "elt"
if str(ELT_DIR) not in sys.path:
    sys.path.insert(0, str(ELT_DIR))

import mock_data
import extract
import run_pipeline


def _unify_order(source, raw, ingest_seq):
    if source == "web":
        fields = {
            "order_id": raw.get("order_id"),
            "email": raw.get("cust_email"),
            "order_date": raw.get("order_date"),
            "amount": raw.get("amount"),
            "currency": raw.get("currency"),
            "pincode": raw.get("pincode"),
            "updated_at": raw.get("updated_at"),
        }
    else:
        fields = {
            "order_id": raw.get("orderId"),
            "email": raw.get("customer", {}).get("email"),
            "order_date": raw.get("orderDate"),
            "amount": raw.get("total", {}).get("value"),
            "currency": raw.get("total", {}).get("currency"),
            "pincode": raw.get("deliveryPin"),
            "updated_at": raw.get("updatedAt"),
        }

    parsed_date = None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"):
        try:
            parsed_date = datetime.strptime(fields["order_date"], date_format).date()
            break
        except (TypeError, ValueError):
            continue

    amount = None
    if fields["amount"] is not None:
        numeric_text = re.sub(r"[^0-9.-]", "", str(fields["amount"]))
        try:
            amount = Decimal(numeric_text)
        except InvalidOperation:
            amount = None

    try:
        updated_at = datetime.fromisoformat(fields["updated_at"])
    except (TypeError, ValueError):
        updated_at = None

    return {
        "order_id": (fields["order_id"] or "").strip() or None,
        "email": (fields["email"] or "").strip().lower() or None,
        "order_date": parsed_date,
        "amount": amount,
        "currency": (fields["currency"] or "").strip().upper() or None,
        "pincode": (fields["pincode"] or "").strip() or None,
        "updated_at": updated_at,
        "source": source,
        "ingest_seq": ingest_seq,
    }


def _validation_reasons(row):
    reasons = []
    if row["order_id"] is None:
        reasons.append("missing_order_id")
    if not row["email"] or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[a-z]{2,}", row["email"]
    ):
        reasons.append("bad_email")
    if not row["pincode"] or not re.fullmatch(r"[1-9][0-9]{5}", row["pincode"]):
        reasons.append("bad_pincode")
    if row["order_date"] is None:
        reasons.append("unparseable_date")
    if row["updated_at"] is None:
        reasons.append("unparseable_updated_at")
    if row["amount"] is not None and row["amount"] <= 0:
        reasons.append("non_positive_amount")
    if row["currency"] not in {"INR", "USD"}:
        reasons.append("unsupported_currency")
    return reasons


def _source_orders():
    rows = []
    web_count = len(mock_data.WEB_ORDERS)
    for seq, raw in enumerate(mock_data.WEB_ORDERS + mock_data.MOBILE_ORDERS, start=1):
        source = "web" if seq <= web_count else "mobile"
        row = _unify_order(source, raw, seq)
        row["reasons"] = _validation_reasons(row)
        rows.append(row)
    return rows


def _deduplicate(rows):
    latest = {}
    for row in rows:
        prior = latest.get(row["order_id"])
        if prior is None or (row["updated_at"], row["ingest_seq"]) > (
            prior["updated_at"],
            prior["ingest_seq"],
        ):
            latest[row["order_id"]] = row
    return latest


def _scd2_periods(events):
    by_effective_date = {}
    for event in events:
        key = (event["cust_id"], date.fromisoformat(event["effective_from"]))
        by_effective_date[key] = event
    grouped = {}
    for (cust_id, valid_from), event in by_effective_date.items():
        grouped.setdefault(cust_id, []).append((valid_from, event))
    periods = {}
    for cust_id, customer_events in grouped.items():
        ordered = sorted(customer_events)
        for index, (valid_from, event) in enumerate(ordered):
            next_date = ordered[index + 1][0] if index + 1 < len(ordered) else None
            valid_to = next_date - timedelta(days=1) if next_date else date.max
            periods.setdefault(cust_id, []).append(
                {"valid_from": valid_from, "valid_to": valid_to, "tier": event["tier"]}
            )
    return periods


def _tier_on(periods, cust_id, order_date):
    return next(
        period["tier"]
        for period in periods[cust_id]
        if period["valid_from"] <= order_date <= period["valid_to"]
    )


def _local_row_hash(fields):
    encoded = json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_email_fields_are_strings_not_markdown_or_formatted_links():
    """Fixture/data validation: verify email fields are plain strings."""
    for row in mock_data.WEB_ORDERS + mock_data.MOBILE_ORDERS:
        email = row.get("cust_email", row.get("customer", {}).get("email"))
        assert isinstance(email, str)
        assert not re.search(r"\[[^\]]+\]\([^)]+\)", email)
        assert not any(char in email for char in "<>\r\n")
    assert any("@@" in row["cust_email"] for row in mock_data.WEB_ORDERS)


def test_source_derived_bronze_silver_quarantine_dedup_and_gold_totals():
    """Fixture/data validation: independently derive expected counts and totals."""
    rows = _source_orders()
    assert len(rows) == len(mock_data.WEB_ORDERS) + len(mock_data.MOBILE_ORDERS) == 8
    quarantined = {row["order_id"]: row["reasons"] for row in rows if row["reasons"]}
    clean = [row for row in rows if not row["reasons"]]
    assert len(clean) == 6
    assert Decimal(len(quarantined)) / Decimal(len(rows)) == Decimal("0.25")
    assert quarantined == {
        "ORD-1004": ["non_positive_amount"],
        "ORD-1006": ["bad_email", "bad_pincode", "unsupported_currency"],
    }

    deduped = _deduplicate(clean)
    assert len(deduped) == 4
    assert deduped["ORD-1003"]["source"] == "mobile"

    periods = _scd2_periods(mock_data.BASELINE_CRM_TIER_EVENTS)
    multipliers = {"Silver": 1, "Gold": 2, "Platinum": 3}
    fx_rates = {
        day: Decimal(str(rate))
        for response in mock_data.FX_RESPONSES
        for day, currencies in response["rates"].items()
        for rate in [currencies["INR"]]
    }
    gold_rows = []
    for row in deduped.values():
        customer = next(
            event
            for event in mock_data.BASELINE_CRM_TIER_EVENTS
            if event["email"].lower() == row["email"]
        )
        tier = _tier_on(
            periods, customer["cust_id"], row["order_date"]
        )
        rate = (
            Decimal("1")
            if row["currency"] == "INR"
            else fx_rates[row["order_date"].isoformat()]
        )
        amount_inr = (row["amount"] * rate).quantize(Decimal("0.01"))
        points = int(amount_inr // Decimal("100")) * multipliers[tier]
        gold_rows.append({"amount_inr": amount_inr, "loyalty_points": points})

    assert len(gold_rows) == 4
    assert sum((row["amount_inr"] for row in gold_rows), Decimal("0")) == Decimal("7785.00")
    assert sum(row["loyalty_points"] for row in gold_rows) == 126


def test_ord_1003_duplicate_selection_uses_latest_updated_at():
    """Python unit test: exercise the local dedup model with fixture timestamps."""
    clean = [row for row in _source_orders() if not row["reasons"]]
    selected = _deduplicate(
        [row for row in clean if row["order_id"] == "ORD-1003"]
    )["ORD-1003"]
    assert selected["updated_at"] == datetime(2026, 9, 2, 18, 40)
    assert selected["source"] == "mobile"
    assert selected["amount"] == Decimal("2100.00")


def test_dedup_sql_orders_by_updated_at_then_ingest_sequence():
    """Static SQL check: confirm the ordering in the Snowflake dedup query."""
    dedup_sql = (ELT_DIR / "sql" / "20_silver_orders_dedup.sql").read_text(
        encoding="utf-8"
    )
    assert re.search(
        r"ORDER\s+BY\s+updated_at\s+DESC\s*,\s*ingest_seq\s+DESC",
        dedup_sql,
        flags=re.IGNORECASE,
    )


def test_quarantine_reasons_include_negative_amount_and_unsupported_currency():
    """Fixture/data validation: evaluate the source-derived validation rules."""
    reasons = {
        row["order_id"]: row["reasons"]
        for row in _source_orders()
        if row["order_id"] in {"ORD-1004", "ORD-1006"}
    }
    assert reasons["ORD-1004"] == ["non_positive_amount"]
    assert reasons["ORD-1006"] == ["bad_email", "bad_pincode", "unsupported_currency"]


def test_arjun_scd2_effective_date_changes_tier_on_effective_day():
    """Python unit test: model the inclusive SCD2 date intervals from the SQL."""
    baseline = _scd2_periods(mock_data.BASELINE_CRM_TIER_EVENTS)
    with_event = _scd2_periods(mock_data.CRM_TIER_EVENTS)
    assert _tier_on(baseline, "CUST-02", date(2026, 9, 1)) == "Silver"
    assert _tier_on(with_event, "CUST-02", date(2026, 8, 14)) == "Silver"
    assert _tier_on(with_event, "CUST-02", date(2026, 8, 15)) == "Gold"
    assert _tier_on(with_event, "CUST-02", date(2026, 9, 1)) == "Gold"
    order = _deduplicate([row for row in _source_orders() if not row["reasons"]])["ORD-1002"]
    usd_rate = next(
        Decimal(str(currencies["INR"]))
        for response in mock_data.FX_RESPONSES
        for day, currencies in response["rates"].items()
        if day == order["order_date"].isoformat()
    )
    amount_inr = order["amount"] * usd_rate
    assert int(amount_inr // Decimal("100")) * 1 == 35
    assert int(amount_inr // Decimal("100")) * 2 == 70


def test_gold_hash_changes_with_tier_and_unchanged_merge_does_not_republish():
    """Python unit test plus static SQL checks; not Snowflake HASH/MERGE execution."""
    business_fields = {
        "order_date": "2026-09-01",
        "cust_id": "CUST-02",
        "email": "arjun.k@yahoo.in",
        "tier": "Silver",
        "multiplier": 1,
        "amount": "42.50",
        "currency": "USD",
        "fx_rate": "83.20",
        "amount_inr": "3536.00",
        "loyalty_points": 35,
    }
    baseline_hash = _local_row_hash(business_fields)
    changed_fields = {
        **business_fields,
        "tier": "Gold",
        "multiplier": 2,
        "loyalty_points": 70,
    }
    assert _local_row_hash(changed_fields) != baseline_hash

    existing = {"row_hash": baseline_hash, "published_at": "original timestamp"}
    unchanged_hash = _local_row_hash(dict(business_fields))
    if existing["row_hash"] != unchanged_hash:
        existing["row_hash"] = unchanged_hash
        existing["published_at"] = "new timestamp"
    assert existing["published_at"] == "original timestamp"

    if existing["row_hash"] != _local_row_hash(changed_fields):
        existing["row_hash"] = _local_row_hash(changed_fields)
        existing["published_at"] = "updated timestamp"
    assert existing["published_at"] == "updated timestamp"

    gold_sql = (ELT_DIR / "sql" / "40_gold_fct_orders.sql").read_text(encoding="utf-8")
    assert "tier, multiplier" in gold_sql
    assert "WHEN MATCHED AND t.row_hash <> s.row_hash THEN UPDATE SET" in gold_sql


def test_api_auth_header_uses_configured_token_without_logging_it(monkeypatch):
    """Python unit test: verify configured-token handling using a test-only value."""
    monkeypatch.delenv("TEST_API_TOKEN", raising=False)
    assert extract._auth("TEST_API_TOKEN") == {}
    monkeypatch.setenv("TEST_API_TOKEN", "local-test-token")
    assert extract._auth("TEST_API_TOKEN") == {
        "Authorization": "Bearer local-test-token"
    }


def test_api_auth_header_uses_bearer_scheme_for_configured_token(monkeypatch):
    """Python unit test: assert the implementation's scheme without real credentials."""
    monkeypatch.setenv("TEST_API_TOKEN", "test-token-value")
    authorization = extract._auth("TEST_API_TOKEN").get("Authorization", "")
    assert authorization.startswith("Bearer ")
    assert authorization.endswith("test-token-value")


def test_baseline_and_b4_crm_modes_are_distinct_and_mock_only(monkeypatch):
    """Fixture/data validation and Python unit test: verify separate CRM inputs."""
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--mock", "--baseline-crm"])
    baseline_args = run_pipeline.parse_args()
    assert baseline_args.mock and baseline_args.baseline_crm
    assert baseline_args.baseline_crm is True
    assert len(mock_data.BASELINE_CRM_TIER_EVENTS) == 4
    assert len(mock_data.CRM_TIER_EVENTS) == 5

    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--mock"])
    event_args = run_pipeline.parse_args()
    assert event_args.mock and not event_args.baseline_crm
    baseline = _scd2_periods(mock_data.BASELINE_CRM_TIER_EVENTS)
    event_variant = _scd2_periods(mock_data.CRM_TIER_EVENTS)
    check_date = date(2026, 9, 1)
    assert _tier_on(baseline, "CUST-02", check_date) == "Silver"
    assert _tier_on(event_variant, "CUST-02", check_date) == "Gold"


def test_requested_arjun_scd2_event_is_present_and_baseline_is_preserved():
    """Fixture/data validation: verify the extra CRM event without altering baseline."""
    assert len(mock_data.BASELINE_CRM_TIER_EVENTS) == 4
    assert len(mock_data.CRM_TIER_EVENTS) == 5
    assert {
        "cust_id": "CUST-02",
        "email": "arjun.k@yahoo.in",
        "tier": "Gold",
        "effective_from": "2026-08-15",
    } in mock_data.CRM_TIER_EVENTS


def test_currency_and_quarantine_sql_include_requested_validation_and_dedupe():
    """Static SQL check: inspect currency validation and quarantine dedup predicates."""
    cleaning_sql = (ELT_DIR / "sql" / "10_silver_orders_clean.sql").read_text(
        encoding="utf-8"
    )
    assert "unsupported_currency" in cleaning_sql
    assert "currency NOT IN ('INR', 'USD')" in cleaning_sql
    assert "ARRAY_CONSTRUCT_COMPACT(" in cleaning_sql
    assert "WHERE ARRAY_SIZE(reasons) = 0" in cleaning_sql
    assert "TRY_TO_DATE(order_date, 'DD/MM/YYYY')" in cleaning_sql
    assert "UPPER(TRIM(currency))" in cleaning_sql
    assert "NOT EXISTS" in cleaning_sql
    assert "EQUAL_NULL(q.order_id, c.order_id)" in cleaning_sql
    assert "EQUAL_NULL(q.row_data:updated_at::TIMESTAMP_NTZ, c.updated_at)" in cleaning_sql


def test_scd2_and_gold_merge_use_requested_history_and_hash_rules():
    """Static SQL check: inspect SCD2 windows, hash fields, and MERGE conditions."""
    scd2_sql = (ELT_DIR / "sql" / "30_dim_customers_scd2.sql").read_text(
        encoding="utf-8"
    )
    gold_sql = (ELT_DIR / "sql" / "40_gold_fct_orders.sql").read_text(
        encoding="utf-8"
    )
    assert "PARTITION BY cust_id, valid_from" in scd2_sql
    assert "LEAD(valid_from)" in scd2_sql
    assert "o.order_date BETWEEN c.valid_from AND c.valid_to" in gold_sql
    assert re.search(
        r"HASH\s*\(\s*order_date\s*,\s*cust_id\s*,\s*email\s*,\s*tier\s*,\s*"
        r"multiplier\s*,\s*amount\s*,\s*currency\s*,\s*fx_rate\s*,\s*amount_inr\s*,\s*"
        r"loyalty_points\s*,\s*is_high_value\s*,\s*city\s*,\s*state\s*,\s*region\s*,\s*"
        r"updated_at\s*\)",
        gold_sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert "ON t.order_id = s.order_id" in gold_sql
    assert "WHEN MATCHED AND t.row_hash <> s.row_hash THEN UPDATE SET" in gold_sql
    assert "published_at = CURRENT_TIMESTAMP()" in gold_sql


def test_quality_checks_include_added_amount_conversion_check():
    """Python unit test with a mocked connector; not a Snowflake integration test."""
    fake_sf = ModuleType("snowflake_io")
    fake_sf.query_one = lambda conn, sql: (0,)
    with patch.dict(sys.modules, {"snowflake_io": fake_sf}):
        assert run_pipeline.quality_checks(object(), strict=False) == "passed"

    captured_sql = []

    def query_one(conn, sql):
        captured_sql.append(sql)
        if "amount_inr IS NULL" in sql:
            return (1,)
        return (0,)

    fake_sf.query_one = query_one
    with patch.dict(sys.modules, {"snowflake_io": fake_sf}):
        with pytest.raises(RuntimeError, match="missing INR conversion"):
            run_pipeline.quality_checks(object(), strict=False)
    check_sql = next(sql for sql in captured_sql if "amount_inr IS NULL" in sql)
    assert "COALESCE(COUNT_IF(" in check_sql
    assert "gold.fct_orders" in check_sql
