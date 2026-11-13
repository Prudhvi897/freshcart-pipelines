# Assignment Checklist

Status definitions: **DONE** means implemented and locally verified where applicable; **IN PROGRESS** means work is prepared but not fully verified; **BLOCKED** means a required external file, service, identity, or evidence is still unavailable.

## DONE

- **A1 — Local repository structure and required files**
  - Present: `README.md`, `.gitignore`, `requirements.txt`, `elt/`, `iris_project/`, `stream/`, `tests/`, `.github/workflows/ci.yml`.
  - `.gitignore` includes `.env`, `*.pkl`, `*.csv`, `mage.log`, and `__pycache__`.
- **A2 — Git command explanations**
  - Drafted in [REPORT_DRAFT.md](REPORT_DRAFT.md).
- **A3 — Local split test and red/green demonstration**
  - `tests/test_prepare_data.py` asserts exact 120/30 counts.
  - Red run: setting `test_size=0.3` failed (`1 failed in 3.13s`, observed train count 105).
  - Green recovery: restoring `0.2` passed (`1 passed in 1.45s`).
- **Part C — Independent local Iris helpers**
  - Loader, validator, trainer, evaluator, and CSV exporter added and unit tested.
  - These are Python utilities only, not a Mage execution.
- **Part B — Local source integration and mock-level checks only (assignment not complete)**
  - Source files are copied into the assignment's `elt/` folder with their original filenames and `sql/` layout; the provided source bundle remains preserved.
  - Added `unsupported_currency`, the requested Arjun Gold CRM event with a retained baseline fixture/CLI switch, a gold amount-without-INR quality check, and microsecond run IDs.
  - Behavior tests independently normalize and validate every supplied mock order, derive Bronze/Silver/quarantine counts and reasons, select deduplicates using `updated_at`/`ingest_seq`, and calculate baseline Gold revenue/points and rejected share from mock FX/CRM/order records. Result: 8/6/2/4 rows, 7,785.00 revenue, 126 points, 25% rejected. These are local fixture-derived checks, not Snowflake output.
  - Tests cover ORD-1003 choosing its later mobile version, ORD-1004/1006 quarantine reasons including unsupported currency, Arjun's inclusive SCD2 effective date, a tier-dependent local row fingerprint, unchanged-row no-republish behavior, and the extra quality check failing on a mocked problem count.
  - Tests are classified in `tests/test_freshcart_source.py`: fixture/data validation (`test_email_fields...`, `test_source_derived...`, `test_quarantine_reasons...`, `test_baseline_and_b4...`, `test_requested_arjun...`); Python unit tests/local models (`test_ord_1003...`, `test_arjun_scd2...`, `test_gold_hash...`, both `test_api_auth...` tests, `test_quality_checks...`); static SQL checks (`test_dedup_sql...`, `test_currency_and_quarantine_sql...`, `test_scd2_and_gold_merge...`). There are **no Snowflake integration tests**; Snowflake verification remains NOT RUN.
  - Email fields were checked as strings without Markdown/HTML formatting; the intentionally malformed `vikram@@mail` remains as source data for validation coverage.
  - The custom web/mobile/CRM endpoints have no API authentication documentation in the supplied files. The code constructs a Bearer authorization header (verified only with a dummy token); whether each endpoint expects Bearer auth is unverified. Frankfurter and India Post calls do not use these token headers.
  - Part B's test helpers use `datetime.strptime`, `datetime.fromisoformat`, and `date.fromisoformat`, all available in Python 3.12; `datetime.strptime('Sep 3, 2026', '%b %d, %Y')` parsed successfully under the active 3.12 interpreter.
  - Baseline and B4 extraction-only mock runs both exited 0 in isolated temporary landing directories: baseline produced 6 web, 2 mobile, 4 CRM, 1 FX records; B4 produced 6 web, 2 mobile, 5 CRM, 1 FX. Both explicitly avoided Snowflake; temporary outputs were removed.
  - All seven SQL files were manually inspected for Snowflake syntax/functions and key transformations. No local Snowflake SQL parser was installed, and SQL was not compiled or executed by Snowflake.
- **Part D — Local RabbitMQ code and mock tests**
  - Dispatcher and driver scripts implement topic publishing, private queues, exact assignment bindings, every-10th malformed payload, malformed JSON rejection, ACK, and NACK without requeue.
  - Startup and two-minute run instructions are in [stream/README.md](stream/README.md).
- **Part E — Report draft and architecture diagram**
  - [REPORT_DRAFT.md](REPORT_DRAFT.md) includes numbered sections, D1 routing, Git command explanations, architecture diagram, reflection draft, and viva prompts. It is explicitly not submission-ready.

## IN PROGRESS

- **A1/A3 — Git identity and remote CI evidence**
  - Six local commits exist, but all show `Copilot <copilot@example.com>`; this is a placeholder, not the student's identity.
  - No remote is configured, no push has occurred, and no GitHub Actions run or screenshots are available.
  - Do not rewrite existing commits without permission; configure the student's real Git author identity before future commits.
- **C — Mage integration**
  - Independent Python modules and tests are ready, but Mage metadata/block conventions have not been verified against the missing course project/runtime.
- **D — Live RabbitMQ verification**
  - Mock tests pass, but local AMQP port 5672 was not listening at the last check. No real broker run or screenshots exist.
- **E — Final report**
  - Draft exists; final PDF is pending real evidence, repository URL, and student identity.

## BLOCKED

- **Part B / B1–B5 — Actual Snowflake pipeline execution and evidence (BLOCKED)**
  - Needed: running Snowflake trial account and local secret configuration for account locator/region, user/authentication, database, schema, warehouse, and role.
  - Required permissions include database/schema/warehouse use, stage/file-format/table setup, and the pipeline's `PUT`/`COPY INTO` operations.
  - Still needed: query outputs/screenshots for baseline counts, before/after ORD-1006 reasons and quarantine count, B4 prediction-vs-actual values, and B5 intentional failure/restoration.
  - The extracted source README warns that the original notebook had a plaintext password that was omitted from the export. Rotate it if it was real and remains active; never provide it in chat or commit it.
- **Original FreshCart notebook**
  - Needed: original course `.ipynb` and any remaining course setup/flow-chart material. The workspace currently has an extracted Python/SQL export and ZIP, not the original notebook.
- **C1–C4 — Mage run and screenshots**
  - Needed: course Mage project export/notebook and Mage runtime/UI access. Cloudflare tunnel details are needed if the UI is remote.
  - Required real evidence: `mage run iris_project iris_classifier --test`, max_depth 1–5 outputs, evaluation branch/metrics, custom Mage block test, and UI graph screenshot.
- **D2/D3 — Broker evidence**
  - Needed: local RabbitMQ service or a broker URL configured privately in `RABBITMQ_URL`; then run dispatcher and at least three drivers for two minutes and capture actual console outputs.
- **E — Submission identity and repository URL**
  - Needed: student's roll number/full name and a GitHub repository URL. No GitHub push will occur without permission.
- **Bonus — Stream-to-lakehouse**
  - Needs both verified RabbitMQ and Snowflake access plus actual integration execution.

## Assignment-provided FreshCart expectations (not execution evidence)

- Bronze: 8 order records (6 web + 2 mobile).
- Clean silver: 6 rows.
- Quarantine: 2 rows (ORD-1004, ORD-1006).
- Deduplicated: 4 rows.
- Gold: 4 orders, revenue 7,785.00, loyalty points 126.
- Rejected share: 25%.

## Current actual verification

- `C:\Users\Prudhvi\AppData\Local\Microsoft\WindowsApps\python3.12.exe -m pytest -q`: **27 passed in 4.28s**.
- Python 3.12.10 `-m compileall -q stream iris_project tests elt`: **PASS**.
- `git diff --check`: **PASS**.
- Isolated baseline dry run with `--baseline-crm`: **exit 0; 6 web, 2 mobile, 4 CRM, 1 FX**.
- Isolated B4 event dry run without `--baseline-crm`: **exit 0; 6 web, 2 mobile, 5 CRM, 1 FX**.
- Git: seven SQL files exist under `elt/sql/`; all seven are currently **untracked** in the worktree, so they are not yet in any commit.
- Python 3.12.10 date checks: `datetime.strptime('Sep 3, 2026', '%b %d, %Y')` -> `2026-09-03`; `date.fromisoformat('2026-08-15')` -> `2026-08-15`.
- SQL syntax: **manual source review only; not validated by Snowflake or a SQL compiler**.
- `Test-NetConnection localhost -Port 5672`: **False**; RabbitMQ is not listening locally.
- GitHub Actions: **NOT VERIFIED**; workflow has not been run on GitHub.
- Snowflake/Mage: **NOT RUN**.
