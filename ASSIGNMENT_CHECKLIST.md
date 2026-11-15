# Assignment Checklist â€” Updated 14 November 2026

**Student:** Prudhvi Raj Kumar  
**Roll number:** 23BCS209  
**Repository:** https://github.com/Prudhvi897/freshcart-pipelines  
**Latest verified commit:** `125f7fb` — `Fix Iris pipeline tests and prediction export`

Status definitions: **DONE** = implemented and verified to the extent stated; **IN PROGRESS** = implemented but a required test, parameter sweep, or evidence item remains; **PENDING EVIDENCE** = work was performed, but a screenshot/output still needs to be attached to the submission.

---

## DONE â€” implementation and execution verified

### Part A â€” Git, tests, and CI
- [x] Repository structure and required project folders/files are present.
- [x] Git remote is configured: `origin` points to the repository URL above.
- [x] Latest commit `48af678` is pushed to `origin/master`.
- [x] Local test suite passed: `27 passed`.
- [x] Red/green split-test demonstration performed: incorrect `test_size=0.3` failed; corrected `0.2` passed.
- [x] Latest GitHub Actions run was reported by the student as successful (green).

### Part B â€” FreshCart ELT and Snowflake
- [x] Pipeline executed with mock source fixtures and an actual Snowflake connection:
  `py -3.12 .\elt\run_pipeline.py --mock --run-date 2026-09-04`
- [x] Snowflake OAuth authentication succeeded; files were staged and Bronze tables loaded.
- [x] Silver and Gold SQL transformations were executed, including cleaning/deduplication, customer SCD2, FX/pincode references, and Gold fact generation.
- [x] Observed extended-run Gold output: 4 orders, â‚¹7,785.00 revenue, 161 loyalty points.
- [x] Data-quality checks for fan-out, duplicate Gold rows, unmatched customers, missing FX, missing city, and missing INR conversion passed.
- [x] Quarantine-rate check reported 25%, above the normal 5% threshold. This warning is disclosed.
- [x] B5 controlled test: baseline Gold missing-INR count was 0; a temporary Gold order with non-NULL amount and NULL amount_inr triggered the new check (1 FAIL); the test row was deleted (0 remaining), and all strict checks passed again. The 27% quarantine threshold was set only in the test process; `.env` was not changed.
- [x] Two pipeline runs were performed. Bronze is append-oriented: 8 raw order rows per run, 16 across both runs.
- [x] Original baseline expectation of 126 loyalty points is distinct from the extended run's 161 points after the additional Arjun/CUST-02 CRM event effective 2026-08-15.

### Part C â€” Mage Iris pipeline
- [x] Mage pipeline `iris_classifier` executed in the Mage Docker image.
- [x] All six block tests passed.
- [x] `iris_predictions.csv` was generated with 30 rows: 29 correct and 1 incorrect (observed accuracy 96.67%).

### Part D â€” RabbitMQ streaming
- [x] Local RabbitMQ broker started in Docker with management UI.
- [x] Dispatcher and six consumer subscriptions were exercised: Ravi, Priya, Arjun, Meena, Karthik, and Control.
- [x] Topic routing was observed for Bangalore and Chennai subscriptions.
- [x] Malformed messages missing zone were rejected with NACK without requeue.
- [x] Management UI was inspected. Overview screenshot showed 6 connections, 6 channels, 8 exchanges, 6 queues, and 6 consumers. Queue screenshot showed running queues with 0 ready and 0 unacknowledged messages at capture time.

---

## IN PROGRESS â€” remaining technical verification

- [ ] **Mage parameter sweep (`max_depth` 1â€“5):** not verified in the available execution record. Run it only if this is explicitly required by the assignment and capture each result.
- [ ] **Mage UI graph screenshot:** not yet confirmed as captured.
- [ ] **Custom Mage block test / any assignment-specific evaluation branch:** verify against the assignment rubric; six pipeline block tests passed, but do not assume this covers every separately specified rubric item.
- [ ] **Original FreshCart notebook:** the original course `.ipynb` was not available in the workspace context; the extracted Python/SQL source bundle was used.

---

## PENDING EVIDENCE â€” collect before submission

- [ ] GitHub repository page showing the project and latest commit.
- [ ] GitHub Actions green run screenshot.
- [ ] Terminal screenshot of red/green split-test demonstration.
- [ ] Snowflake pipeline terminal output.
- [ ] Snowflake query/result screenshot showing 4 Gold orders, â‚¹7,785.00 revenue, and 161 points for the extended run; label the baseline 126-point expectation separately.
- [ ] Snowflake quality-check output showing the 25% quarantine warning and other check results.
- [ ] Mage terminal output showing all six block tests passed.
- [ ] `iris_predictions.csv` preview.
- [ ] RabbitMQ Overview screenshot.
- [ ] RabbitMQ Queues/Consumers screenshot.
- [ ] Representative RabbitMQ consumer logs showing routing and NACK behavior.
- [ ] Final PDF named according to the assignment's required naming convention.

---

## Important accuracy notes

1. **Mock source data vs Snowflake execution:** source extraction used mock fixtures (`--mock`), but OAuth authentication, staging, loading, and SQL transformations ran against Snowflake. Do not describe this as live production API ingestion.
2. **Loyalty points:** 126 is the assignment's original baseline expectation. 161 is the observed extended run after the additional Arjun/CUST-02 CRM event. State which scenario each number represents.
3. **Bronze counts:** 8 order records were loaded per pipeline run (6 web + 2 mobile). Two runs produced 16 raw order rows in the append-oriented Bronze history.
4. **Quarantine:** the 25% quarantine rate exceeded the configured 5% threshold and should be reported as a warning.
5. **Mage accuracy:** 29 of 30 predictions were correct in the generated CSV; one row was misclassified.
6. **Do not claim unverified work:** the `max_depth` 1â€“5 sweep, Mage UI graph screenshot, and any rubric-specific custom test/evaluation branch remain unverified until evidence is captured.

---

## Useful verification commands

```powershell
py -3.12 -m pytest -q
git status --short
git log -5 --oneline
```

Mage run:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/home/src" --workdir /home/src --entrypoint mage mageai/mageai:latest run iris_project iris_classifier --test
```


