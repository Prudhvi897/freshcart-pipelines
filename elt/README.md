# FreshCart Snowflake ELT

The supplied course Python and SQL files have been integrated under this `elt/` directory, preserving their filenames and `sql/` layout. The source bundle at `freshcart_elt_source/freshcart_elt_extracted/` is preserved as supplied. The original course `.ipynb` is not present; its extracted README identifies it as `freshcart_elt_colab (1).ipynb`. Integrated code is source material, not proof of Snowflake execution.

The assignment's intended flow is:

```text
Extract sample API data -> raw files
Load raw files (PUT + COPY INTO) -> bronze
Transform -> silver / dimensions and references / gold
Check -> quality_checks()
```

See [SQL_TEMPLATES.md](SQL_TEMPLATES.md) for the exact SQL behavior, implemented unsupported-currency change, expected values quoted from the assignment, record traces, and unverified execution steps.

## Run the mock pipeline

The local extraction-only check runs without Snowflake and does not create database results:

```powershell
python run_pipeline.py --dry-run --mock --run-date 2026-09-04
```

For the Part B1 baseline with Snowflake configured in `.env`, the preserved baseline CRM fixture is selected with:

```powershell
python run_pipeline.py --setup --mock --baseline-crm --run-date 2026-09-04
```

After completing the baseline, run the Part B4 event variant with:

```powershell
python run_pipeline.py --mock --run-date 2026-09-04
```

The latter mock uses both Arjun CRM tier events, including the requested Gold event effective 2026-08-15. These full commands perform Snowflake operations; do not run them until credentials, permissions, and your intended Snowflake account are confirmed. The baseline and B4 database states are not simultaneously reproducible in the same schema without restoring/resetting the CRM data as needed.

## Needed to continue

1. The original FreshCart `.ipynb` downloaded from the course, if available, plus any setup instructions/flow chart not included in the extracted bundle.
2. A Snowflake trial account and a role/warehouse with the database, schema, stage, file-format, and table permissions needed by `sql/00_setup.sql` and the pipeline.
3. Configure secrets locally (not in Git): account locator/region, user and authentication method, database, schema, warehouse, and role. The extracted `snowflake_io.py` supports password, SSO authenticator, or private-key environment configuration; do not send passwords, keys, or tokens in chat.
4. The extracted README warns that a plaintext password existed in the original notebook but was intentionally omitted from the source export. If that credential was real and remains active, rotate it immediately.

Once supplied, run the course notebook or integrated mock pipeline in the configured Snowflake account and record actual results separately from assignment-provided expectations. The `--dry-run --mock` output verifies extraction only and is not Snowflake validation.
