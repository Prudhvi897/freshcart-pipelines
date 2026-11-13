# FreshCart SQL templates (not executed)

The course Python/SQL has been integrated under `elt/`; the supplied source copy at `freshcart_elt_source/freshcart_elt_extracted/` is preserved. The original notebook is still absent. The source has **not** been run in Snowflake. This document distinguishes assignment expectations/source-derived calculations from actual results.

## Required baseline (assignment-provided expectations, not observed results)

| Check | Expected after one run |
|---|---:|
| Bronze raw orders | 8 (6 web + 2 mobile) |
| Silver cleaned orders | 6 |
| Quarantine | 2: ORD-1004, ORD-1006 |
| Deduplicated orders | 4 |
| Gold orders | 4 |
| Gold revenue | 7,785.00 |
| Gold loyalty points | 126 |
| Rejected row share | 25% |

These values come from the assignment PDF. No actual Snowflake results are available in this repository.

## Bronze to normalized checked rows

The extracted `mock_data.py` and `sql/10_silver_orders_clean.sql` show that the web source is flat while the mobile source is nested/camelCase. The exact extracted mappings are:

```sql
SELECT
    raw:order_id::STRING   AS order_id,
    raw:cust_email::STRING AS cust_email,
    raw:cust_name::STRING  AS cust_name,
    raw:order_date::STRING AS order_date,
    raw:amount::STRING     AS amount,
    raw:currency::STRING   AS currency,
    raw:pincode::STRING    AS pincode,
    raw:updated_at::STRING AS updated_at
FROM bronze.orders_raw
WHERE source = 'web'
UNION ALL
SELECT
    raw:orderId::STRING,
    raw:customer.email::STRING,
    raw:customer.name::STRING,
    raw:orderDate::STRING,
    raw:total.value::STRING,
    raw:total.currency::STRING,
    raw:deliveryPin::STRING,
    raw:updatedAt::STRING
FROM bronze.orders_raw
WHERE source = 'mobile';
```

The following extracted SQL then normalizes email with `LOWER(TRIM(...))`, name with `INITCAP`, dates with `COALESCE(TRY_TO_DATE(...))`, amount with `TRY_TO_DECIMAL(REGEXP_REPLACE(amount, '[^0-9.-]', ''), 12, 2)`, and currency with `UPPER(TRIM(currency))`.

### ORD-1003 trace

The extracted `mock_data.py` contains these two source records:

- Web: `order_id=ORD-1003`, `cust_email=meera@outlook.com`, `amount=null`, `currency=INR`, `updated_at=2026-09-02 09:10:00`.
- Mobile: `orderId=ORD-1003`, nested `customer.email=Meera@Outlook.com`, `total.value=2,100.00`, `total.currency=INR`, `updatedAt=2026-09-02T18:40:00`.

The `UNION ALL` maps both into the common order columns. `TRY_TO_TIMESTAMP_NTZ` parses the timestamps. `sql/20_silver_orders_dedup.sql` uses `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, ingest_seq DESC) = 1`, so the later mobile row ranks first for ORD-1003.

The extracted gold SQL uses INR rate 1.0, `amount_inr = ROUND(amount * fx.rate_to_inr, 2)`, and `loyalty_points = FLOOR(amount_inr / 100) * multiplier`. Using the extracted mock values and multiplier reference, ORD-1003 is `ROUND(2100 * 1.0, 2) = 2,100.00` INR; Meera's Platinum multiplier is 3, so `FLOOR(2100 / 100) * 3 = 63` points. These are SQL/data-derived expected values, not Snowflake execution results.

### ORD-1005 and ORD-1001 tier trace

The extracted `dim.customers_scd2` creates inclusive effective periods; gold joins customers by normalized email and `o.order_date BETWEEN c.valid_from AND c.valid_to`, then joins `ref.tier_multiplier` on `m.tier = c.tier`. Priya's Gold event starts on 2026-09-03, so ORD-1005 (2026-09-03) is Gold; ORD-1001 (2026-09-01) is Silver. The extracted reference multipliers are Silver 1 and Gold 2. Thus ORD-1005's `899 INR` gives `FLOOR(899 / 100) * 2 = 16` points; ORD-1001's `1,250 INR` gives `FLOOR(1250 / 100) * 1 = 12` points. These calculations are derived from the extracted mock inputs and SQL, not from Snowflake.

## Cleaning reasons and quarantine

The preserved source copy's `sql/10_silver_orders_clean.sql` did not contain the currency reason. The integrated `elt/sql/10_silver_orders_clean.sql` now includes this expression inside `ARRAY_CONSTRUCT_COMPACT` after the amount validation:

```sql
IFF(currency IS NULL OR currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)
```

`currency` is already normalized to uppercase in the `typed` CTE. For ORD-1006, the mock has an invalid email and five-digit pincode `99999`; evaluating the existing validation expressions gives `["bad_email", "bad_pincode"]` before the change and `["bad_email", "bad_pincode", "unsupported_currency"]` after it. It remains excluded from `silver.orders_clean`, so this validation change alone should not alter gold totals. This comparison is derived from source logic, not a Snowflake query.

The extracted quarantine insert uses `NOT EXISTS` matching `q.source = c.source`, `EQUAL_NULL(q.order_id, c.order_id)`, and `EQUAL_NULL(q.row_data:updated_at::TIMESTAMP_NTZ, c.updated_at)`, followed by `QUALIFY ROW_NUMBER()` over source/order/update timestamp. That is the condition to verify for duplicate prevention. Since the old quarantine row is not updated by this `INSERT`, inspect `silver.orders_checked` for the new reasons and separately check whether the prior quarantine row retains its old reasons.

## Deduplication

The extracted `sql/20_silver_orders_dedup.sql` uses this exact deduplication selection:

```sql
SELECT *
FROM silver.orders_clean
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC, ingest_seq DESC
) = 1;
```

For each order, `ROW_NUMBER()` ranks the most recently updated row first; `ingest_seq` breaks timestamp ties deterministically. `QUALIFY ... = 1` retains only that top-ranked row.

## SCD2, loyalty and gold

`BASELINE_CRM_TIER_EVENTS` preserves the original CUST-02 Silver event effective 2024-01-15. `CRM_TIER_EVENTS` adds the requested Arjun Gold event effective 2026-08-15. Use `--baseline-crm` for the B1 baseline and omit it for the B4 event variant. The integrated runner has a microsecond component in each `run_id`, ensuring generated landing filenames do not collide for separate runs within one second. The SCD2 SQL partitions duplicate events by `(cust_id, valid_from)`, creates `valid_to` as the day before the next change, and marks the final event current. Fill your prediction column before running; do not fill actual values until querying Snowflake.

| Quantity | Your prediction (fill before execution) | Actual Snowflake result |
|---|---|---|
| CUST-02 rows in `dim.customers_scd2` |  | NOT RUN |
| Tier selected for ORD-1002 |  | NOT RUN |
| Loyalty points for ORD-1002 |  | NOT RUN |
| Total gold loyalty points |  | NOT RUN |
| Gold rows whose `published_at` changed |  | NOT RUN |

The Gold merge matches on `t.order_id = s.order_id` and updates only when `t.row_hash <> s.row_hash`. `row_hash` hashes order date, customer/email, tier/multiplier, amount/currency/FX, derived values, geography, and `updated_at`; a changed Arjun tier should therefore change ORD-1002's hash, and the update sets its `published_at` to the current timestamp. Same-key, same-hash rows are not updated on a rerun. Actual row counts and timestamp changes still require querying Snowflake.

## Gold idempotency / row hash

The extracted loader says Snowflake `COPY` skips a previously loaded identical staged filename (for up to its file-load retention window). Each pipeline run generates a new `run_id` and new landing filenames, so each run's 6 web + 2 mobile records are new files and bronze grows by 8. This differs from rerunning the same `COPY` for the exact same filename.

## Additional quality check

The supplied runner already had six checks (fan-out, duplicate gold keys, unmatched customers, missing FX, missing city, and quarantine rate). The integrated runner adds the requested amount-present/INR-conversion-missing check as a seventh overall check, without deleting supplied checks. One approved query is:

```sql
SELECT COALESCE(COUNT_IF(amount IS NOT NULL AND amount_inr IS NULL), 0) AS problem_count
FROM gold.fct_orders;
```

The check is implemented in `elt/run_pipeline.py` as a failing-quality condition and is covered with a mocked Snowflake connector in local tests. No Snowflake operations were executed. Insert a mock row using the real table schema to make it fail, capture actual `PROBLEM` output, remove the row, and rerun in Snowflake.

## Snowflake access and files needed

The workspace includes the extracted source tree at `freshcart_elt_source/freshcart_elt_extracted/` and an archive named `freshcart_elt_source.zip`; the original `.ipynb` itself is absent. The extracted README warns that a plaintext password existed in the original notebook but is intentionally omitted from the source export; rotate that credential if it was real and remains active. For execution, configure the account locator/region, user/authentication method, database, schema, warehouse, and role locally or in a secret manager. Do not send passwords, keys, or tokens in chat or commit them to Git. The role needs permission to create/use the warehouse/database/schemas, internal stage, tables, and file formats, and to run `PUT`/`COPY INTO`.
