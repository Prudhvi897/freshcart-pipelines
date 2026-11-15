# From Git to Gold â€” Data Engineering Pipeline Orchestration Report

**Student:** Prudhvi Raj Kumar  
**Roll number:** 23BCS209  
**GitHub repository:** https://github.com/Prudhvi897/freshcart-pipelines  
**Submission date:** 14 November 2026

## 1. Project overview

This project implements four connected data engineering components:

1. Git version control, automated tests, and GitHub Actions CI.
2. FreshCart ELT ingestion and transformation using Snowflake.
3. Iris classification using a Mage orchestration pipeline.
4. Event routing and consumer handling using RabbitMQ.

The work demonstrates source control, data validation, transformation, orchestration, model evaluation, message routing, and failure handling. Source API responses for FreshCart were supplied through mock fixtures; Snowflake authentication, staging, loading, and SQL execution were performed against Snowflake.

## 2. Part A â€” Git, tests, and CI

### A1. Repository and commit history

Repository: https://github.com/Prudhvi897/freshcart-pipelines  
Branch: `master`  
Latest verified commit: `125f7fb` â€” `Fix Iris pipeline tests and prediction export`

The work was organized into meaningful commits, including:

| Commit | Work |
|---|---|
| `8bbcff7` | Add FreshCart ELT, Mage Iris, and RabbitMQ pipelines |
| `48af678` | Complete Mage Iris classification pipeline |
| `3b06db4` | Add custom Mage evaluation summary block |
| `125f7fb` | Fix Iris pipeline tests and prediction export |

The repository also contains earlier test/import-path work. The latest verified commit was pushed to `origin/master`.

### A2. Git commands and collaboration

| Command | Purpose |
|---|---|
| `git init` | Initialize a local Git repository |
| `git add .` | Stage selected working-tree changes |
| `git commit -m "message"` | Save a commit in the local repository |
| `git remote add origin URL` | Connect the local repository to a remote |
| `git push -u origin master` | Publish local commits to the remote branch |
| `git pull` | Fetch and integrate remote changes |

A local commit is not automatically visible to teammates because it exists only in the local repository. The commit becomes available through the shared remote after it is pushed.

### A3. Automated testing and CI

Local tests were run with:

```powershell
py -3.12 -m pytest -q
```

**Result: 27 passed, 1 warning.**

A red/green test demonstration was performed. The deliberately incorrect `test_size=0.3` caused the test to fail; correcting it to `0.2` made the test pass. GitHub Actions also completed successfully for commit `125f7fb`.

**Evidence:** `evidence/A_github_actions_pass.png`

## 3. Part B â€” FreshCart ELT and Snowflake

### B1. Pipeline and baseline counts

The pipeline was executed using:

```powershell
py -3.12 .\elt\run_pipeline.py --mock --run-date 2026-09-04
```

The original logical batch contains eight source orders: six web records and two mobile records.

| Stage or measure | Baseline result |
|---|---:|
| Bronze raw orders | 8 |
| Silver clean orders | 6 |
| Quarantined orders | 2 |
| Deduplicated orders | 4 |
| Gold fact orders | 4 |
| Gold revenue | â‚¹7,785.00 |
| Gold loyalty points | 126 |
| Quarantine share | 25% |

The two quarantined orders in the baseline are ORD-1004 and ORD-1006. The quarantine share is 2 out of 8, or 25%.

### B2. Trace ORD-1003 and ORD-1005

**ORD-1003 â€” two API versions**

The web API provides a flat record with `order_id`, `cust_email`, `amount`, and related fields. Its ORD-1003 record has a NULL amount and `updated_at` of 2 September 2026 at 09:10.

The mobile API provides nested fields such as `orderId`, `customer.email`, and `total.value`. Its ORD-1003 record has an amount of â‚¹2,100 and a later update time of 18:40 on the same date.

The SQL in `10_silver_orders_clean.sql` maps both API shapes into common columns in `silver.orders_checked`. The later mobile version wins in `silver.orders_dedup`, because the query uses `ROW_NUMBER()` partitioned by `order_id`, ordered by `updated_at DESC` and then `ingest_seq DESC`.

Meera's tier is Platinum, with a multiplier of 3. The winning order therefore earns:

`FLOOR(2100 / 100) Ã— 3 = 63 loyalty points`.

**ORD-1005 â€” point-in-time customer tier**

ORD-1005 belongs to Priya (`priya.r@gmail.com`) and is dated 3 September 2026. The amount string contains a rupee symbol and is converted to the numeric amount â‚¹899 by the SQL numeric-cleaning expression.

Priya's Gold tier becomes effective on 3 September 2026. Gold has a multiplier of 2, so ORD-1005 earns:

`FLOOR(899 / 100) Ã— 2 = 16 loyalty points`.

For comparison, ORD-1001 is dated 1 September 2026, when Priya's tier is still Silver. Its â‚¹1,250 amount and multiplier of 1 produce 12 points.

The point-in-time join in `40_gold_fct_orders.sql` matches the order date against the customer's `valid_from` and `valid_to` period. Therefore, the tier is determined by the order date, not simply the customer's latest tier.

### B3. Unsupported currency validation

The cleaning SQL normalizes currency with `UPPER(TRIM(currency))` and accepts only INR and USD. A record with an unsupported currency, such as EUR, receives the `unsupported_currency` reason through `ARRAY_CONSTRUCT_COMPACT`.

Rows with validation reasons are excluded from `silver.orders_clean` and inserted into `quarantine.orders`. The quarantine insert uses a `NOT EXISTS` condition on source, order ID, and update timestamp to avoid inserting the same invalid source/order version again on a later run. This retains invalid data for investigation without allowing it into the clean transformation path.

### B4. Arjun's SCD Type 2 change

Arjun (`CUST-02`, `arjun.k@yahoo.in`) has two CRM tier events in the extended fixture:

| Tier | Valid from | Valid to | Current |
|---|---|---|---|
| Silver | 2024-01-15 | 2026-08-14 | No |
| Gold | 2026-08-15 | 9999-12-31 | Yes |

The SCD Type 2 transformation uses `LEAD(valid_from)` to set the end of each previous period to the day before the next tier event. The final event has an open-ended validity date of 9999-12-31.

ORD-1002 is dated 1 September 2026, so it joins to Arjun's Gold version. Its USD 42.50 amount is converted using the 1 September FX rate of â‚¹83.20 per USD:

`42.50 Ã— 83.20 = â‚¹3,536.00`

With the Gold multiplier of 2, loyalty points are:

`FLOOR(3536 / 100) Ã— 2 = 70`.

The Silver multiplier would have produced 35 points, so the tier change adds 35 points for this order.

The extended fixture includes the additional Arjun Gold event. Its observed total of 161 loyalty points is therefore distinct from the original baseline total of 126 points. The two scenarios must not be treated as the same run configuration.

The SCD2 event query deduplicates repeated copies of the same customer/effective-date event. The Gold `MERGE` matches on `order_id` and compares a `row_hash` of business values. An unchanged row is not updated on an identical rerun. If the hash changes, the matched row is updated and `published_at` is refreshed. This makes publication idempotent for unchanged data.

### B5. Deliberate Gold quality-check failure and recovery

A new quality check was added to detect Gold orders where `amount` is present but `amount_inr` is NULL.

The test inserted a temporary synthetic Gold order named `B5-GOLD-TEST-ONLY`, with `amount = 100` and `amount_inr = NULL`.

The pre-existing quarantine rate was 25%, above the normal configured 5% threshold. To isolate the new check, the test process temporarily set `QUARANTINE_MAX_RATE` to 27%. The project's `.env` file and normal threshold were not changed.

- **Baseline:** missing-INR count was 0 and strict checks passed.
- **Deliberate failure:** the synthetic order made the missing-INR count 1, and strict mode raised the expected quality-check failure.
- **Cleanup:** the temporary order was deleted, and a follow-up query confirmed zero remaining test rows.
- **Recovery:** the missing-INR count returned to 0 and strict checks passed again.

This demonstrates that the new check detects a Gold conversion defect and that the table returns to its passing state after the test row is removed.

**Evidence:** `evidence/B5_gold_quality_check.txt`

### ELT versus ETL

In this project, source data is first extracted and loaded into Snowflake Bronze tables. Cleaning, deduplication, SCD2 construction, enrichment, and Gold publication then happen inside Snowflake using SQL. This is ELT: extract, load, transform. In ETL, transformation would occur before loading the transformed result into the target warehouse.

### Execution scope and quality results

The source responses were mock fixtures. Snowflake OAuth authentication, staging, loading, and SQL transformations were executed against Snowflake. The pipeline was run twice; append-oriented Bronze ingestion therefore recorded 16 raw order rows across both runs.

The quality checks reported zero fan-out, duplicate Gold order IDs, unmatched customers, missing FX rates, missing city mappings, and missing INR conversions. The quarantine-rate check warned at 25%, above the configured 5% threshold. This warning is reported rather than hidden.

## 4. Part C â€” Mage Iris classification pipeline

### C1. Pipeline structure and execution

The Mage pipeline `iris_classifier` contains seven blocks:

1. `load_iris`
2. `validate_data`
3. `prepare_data`
4. `train_model`
5. `evaluate_model`
6. `save_results`
7. `summarize_evaluation`

The main dependency path is:

`load_iris â†’ validate_data â†’ prepare_data â†’ train_model`

The training block branches to `evaluate_model` and `save_results`. The evaluation output then feeds `summarize_evaluation`.

The pipeline was executed in the Mage Docker image. The completed run reported all seven blocks with their tests passing.

**Evidence:** `evidence/C1_mage_pipeline_graph.png`

### C2. Maximum-depth sweep and test behavior

The `max_depth` parameter was tested at values 1 through 5. Each run produced 30 predictions, with 29 correct predictions.

| max_depth | Correct | Total | Accuracy | Mage tests |
|---:|---:|---:|---:|---|
| 1 | 29 | 30 | 96.67% | 6/6 passed |
| 2 | 29 | 30 | 96.67% | 6/6 passed |
| 3 | 29 | 30 | 96.67% | 6/6 passed |
| 4 | 29 | 30 | 96.67% | 6/6 passed |
| 5 | 29 | 30 | 96.67% | 6/6 passed |

These five sweep runs were performed before the seventh custom summary block was added. Each sweep run passed the six then-existing block tests.

A failing `@test` on the training block causes Mage to mark that block as failed. Downstream blocks such as `save_results` do not execute, preventing invalid training output from being saved or propagated.

**Evidence:** `evidence/C2_max_depth_sweep.csv`

### C3. Evaluation metrics and confusion matrix

The evaluation block calculates accuracy, weighted precision, weighted recall, weighted F1, and a confusion matrix.

| Metric | Result |
|---|---:|
| Accuracy | 0.9667 |
| Weighted precision | 0.9694 |
| Weighted recall | 0.9667 |
| Weighted F1 | 0.9667 |

Confusion matrix:

```text
[[7,  0,  0],
 [0, 11,  0],
 [0,  1, 11]]
```

There was one misclassification: one sample from class 2 was predicted as class 1. The other 29 predictions were correct.

**Evidence:** `evidence/C3_evaluation_metrics.txt`

### C4. Custom evaluation summary block

A custom transformer, `summarize_evaluation`, was added after `evaluate_model`. It reads the evaluation metrics and returns accuracy, a performance label, class count, and confusion matrix.

The performance label is assigned as follows:

- Accuracy at least 0.90: `excellent`
- Accuracy at least 0.75: `good`
- Otherwise: `needs_improvement`

Its `@test` checks that accuracy is between 0 and 1, the class count is three, the performance label is valid, and the confusion matrix has three rows.

The full seven-block pipeline was run after adding this block, and all seven block tests passed. The resulting summary reported accuracy 0.9667 and performance `excellent`.

**Evidence:** `evidence/C4_summary_output.json`

## 5. Part D â€” RabbitMQ event streaming

### D1. Topic routing table

The dispatcher publishes routing keys to the `rapido-dispatch` topic exchange. The consumer bindings use exact routing keys and the RabbitMQ topic wildcards `*` and `#`.

| Routing key | Matching consumers |
|---|---|
| `bangalore.koramangala.food` | Ravi, Meena, Control |
| `bangalore.indiranagar.ride` | Priya, Arjun, Control |
| `bangalore.whitefield.ride` | Arjun, Control |
| `chennai.tnagar.food` | Karthik |
| `chennai.whitefield.ride` | None; dropped if no matching binding exists |
| `bangalore.koramangala` | Control only |

The `*` wildcard matches exactly one routing-key word. The `#` wildcard matches zero or more words. Thus `bangalore.#` can match both `bangalore.koramangala.food` and the two-word key `bangalore.koramangala`. Bindings containing `*` in a three-word pattern do not match that two-word key.

### D2. Dispatcher and consumers

A local RabbitMQ broker was run in Docker with the management plugin enabled. The dispatcher published events to the `rapido-dispatch` topic exchange, and six consumers subscribed using their respective bindings.

| Consumer | Binding | Responsibility |
|---|---|---|
| Ravi | `bangalore.koramangala.*` | Koramangala food and ride events |
| Priya | `bangalore.indiranagar.*` | Indiranagar food and ride events |
| Arjun | `bangalore.*.ride` | Bangalore ride events across zones |
| Meena | `bangalore.*.food` | Bangalore food events across zones |
| Karthik | `chennai.tnagar.food` | Chennai T. Nagar food events |
| Control | `bangalore.#` | All Bangalore routing keys matching the pattern |

The saved routing evidence contains representative delivery examples for the consumers. The management Overview screenshot showed six connections, six channels, eight exchanges, six queues, and six consumers. The queues view showed zero ready and zero unacknowledged messages at the time of capture.

**Evidence:** `evidence/D1_rabbitmq_overview.png`, `evidence/D2_consumer_routing.txt`, `evidence/D2_rabbitmq_queues.png`, and `evidence/D3_rabbitmq_exchange_bindings.png`

### D3. NACK, requeue, and consumer failure

Messages without a required zone were rejected by the relevant consumers with NACK and `requeue=False`. This avoids repeatedly delivering a message that is known to be invalid.

If a consumer crashes before acknowledging a delivery, RabbitMQ can requeue the unacknowledged message when the channel or connection closes. Another consumer can then receive it. This supports reliable delivery, but consumers should be designed to handle possible duplicate processing.

Using `requeue=True` for a permanently invalid message can create a poison-message loop: the same message is repeatedly delivered, rejected, and requeued. A dead-letter queue or rejection without requeue is more appropriate for messages that cannot be processed.

**Evidence:** `evidence/D3_invalid_message_handling.txt`

## 6. Integration diagram

```text
                 GitHub repository
                        |
                GitHub Actions CI
                        |
          +-------------+-------------+
          |             |             |
      FreshCart       Mage          RabbitMQ
       ELT/SQL       Iris ML       dispatcher
          |             |             |
       Snowflake    Predictions    Topic exchange
      Bronze/Silver    CSV          /   |   \
        / Gold       Metrics     Consumers
          |             |        and routing
          +-------------+-------------+
                        |
               Tested data outputs
               and saved evidence
```

The components demonstrate different parts of a data engineering workflow: versioned code and CI, warehouse ingestion and transformation, orchestrated machine learning, and asynchronous event distribution.

## 7. Reflection

One useful failure exercise was the deliberate B5 Gold quality-check test. The first challenge was separating the new missing-INR check from the existing quarantine-rate warning. The original fixture has a 25% quarantine rate, while the normal strict threshold is 5%. Without isolating that pre-existing condition, a strict test could fail for the wrong reason and make it unclear whether the new check was working.

I used a temporary process-level threshold of 27% for the test only, inserted a synthetic Gold order with an amount but no INR conversion, and confirmed that the new check failed with a count of one. I then removed the synthetic row and confirmed that the count returned to zero and strict checks passed. The `.env` threshold was left unchanged.

This exercise showed why a good quality test must isolate the condition it intends to test, verify both failure and recovery, and clean up its test data. It also reinforced the importance of reporting warnings honestly rather than changing normal project settings to make a run appear successful.

## 8. Reproducibility and evidence index

Useful verification commands:

```powershell
py -3.12 -m pytest -q
git status --short
git log -5 --oneline
```

Mage pipeline test command:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/home/src" --workdir /home/src --entrypoint mage mageai/mageai:latest run iris_project iris_classifier --test
```

Evidence files:

| Assignment area | Evidence file |
|---|---|
| A â€” GitHub Actions | `evidence/A_github_actions_pass.png` |
| B5 â€” Gold quality check | `evidence/B5_gold_quality_check.txt` |
| C1 â€” Mage graph | `evidence/C1_mage_pipeline_graph.png` |
| C2 â€” Depth sweep | `evidence/C2_max_depth_sweep.csv` |
| C3 â€” Evaluation metrics | `evidence/C3_evaluation_metrics.txt` |
| C4 â€” Custom summary output | `evidence/C4_summary_output.json` |
| D1 â€” RabbitMQ overview | `evidence/D1_rabbitmq_overview.png` |
| D2 â€” Consumer routing | `evidence/D2_consumer_routing.txt` |
| D2 â€” Queues screenshot | `evidence/D2_rabbitmq_queues.png` |
| D3 â€” Invalid message handling | `evidence/D3_invalid_message_handling.txt` |
| D3 â€” Exchange bindings | `evidence/D3_rabbitmq_exchange_bindings.png` |

## 9. Conclusion

The project implements and tests the Git/CI, FreshCart Snowflake ELT, Mage Iris, and RabbitMQ components. It demonstrates data cleaning and quarantine, deduplication, effective-dated customer dimensions, idempotent Gold publication, ML evaluation and testing, and topic-based message routing with explicit invalid-message handling.

The report distinguishes mock source fixtures from the real Snowflake execution, the original 126-point baseline from the extended 161-point result, and the 25% quarantine warning from the isolated B5 quality-check test. The evidence index identifies the saved artifacts supporting the implementation and its verification.

