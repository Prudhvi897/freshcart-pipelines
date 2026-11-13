# Assignment Checklist

This checklist tracks the assignment requirements from the PDF and the current implementation state. Use the assigned statuses exactly: NOT STARTED, IN PROGRESS, IMPLEMENTED, TESTED, VERIFIED, BLOCKED.

## Part A: Git and CI/CD

- [ ] A1. Repository scaffold and structure — IMPLEMENTED
  - Relevant files: README.md, .gitignore, requirements.txt, .github/workflows/ci.yml, tests/test_prepare_data.py
  - Evidence: local repository initialized and repo structure created.
  - Manual actions remaining: create a GitHub remote and push only with explicit permission.

- [ ] A1. At least five meaningful commits — IN PROGRESS
  - Relevant files: git log output in final report.
  - Evidence: repository is being committed in stages as work is completed.
  - Manual actions remaining: final `git log --oneline` extraction when project is complete.

- [ ] A2. Git command explanations — IMPLEMENTED (template prepared)
  - Relevant files: README.md and final report.
  - Evidence: command explanations will be written in the final PDF report.
  - Manual actions remaining: convert explanations into the final report document.

- [ ] A3. Test for prepare_data — IMPLEMENTED
  - Relevant files: tests/test_prepare_data.py
  - Evidence: `python -m pytest -q` passes.

- [ ] A3. GitHub Actions workflow — IMPLEMENTED
  - Relevant files: .github/workflows/ci.yml
  - Evidence: YAML exists with Python 3.12 setup and pytest step.
  - Manual actions remaining: push to GitHub and view Action logs.

## Part B: FreshCart ELT on Snowflake

- [ ] B1. Baseline pipeline notebook and expected values — BLOCKED
  - Relevant files: elt/
  - Evidence: project scaffold is present, but actual Snowflake notebook execution requires a live Snowflake trial account and credentials.
  - Manual actions remaining: connect to own Snowflake account, run notebook, capture screenshots.

- [ ] B2. ORD-1003 and ORD-1005 trace — BLOCKED
  - Relevant files: elt/
  - Evidence: assignment-specific SQL and outputs are not available in the current workspace.
  - Manual actions remaining: run the provided FreshCart notebook in Snowflake and document the trace.

- [ ] B3. Unsupported currency validation — BLOCKED
  - Relevant files: elt/
  - Evidence: SQL logic not present in a live Snowflake project.
  - Manual actions remaining: apply the rule in the live notebook and verify with actual SQL.

- [ ] B4. SCD2 change and idempotency — BLOCKED
  - Relevant files: elt/
  - Evidence: no Snowflake schema or SQL files are present.
  - Manual actions remaining: add the event, run the pipeline, and compare predictions vs actuals.

- [ ] B5. Sixth data-quality check — BLOCKED
  - Relevant files: elt/
  - Evidence: the notebook is not present.
  - Manual actions remaining: add the check, run it, intentionally break it, and restore.

## Part C: Mage ML pipeline

- [ ] C1. Pipeline graph and run — BLOCKED
  - Relevant files: iris_project/
  - Evidence: repository scaffold exists, but no Mage runtime or metadata is connected to a live Mage instance.
  - Manual actions remaining: run `mage run iris_project iris_classifier --test` from a configured Mage environment.

- [ ] C2. Test gate experiment — BLOCKED
  - Relevant files: iris_project/
  - Evidence: no live Mage runtime available here.
  - Manual actions remaining: run the pipeline for max_depth 1..5 and capture accuracy and CSV generation evidence.

- [ ] C3. Evaluation branch — BLOCKED
  - Relevant files: iris_project/
  - Evidence: metadata file is a scaffold only.
  - Manual actions remaining: add evaluate_model in the live Mage UI or project files and capture screenshots.

- [ ] C4. Own block — BLOCKED
  - Relevant files: iris_project/
  - Evidence: no live Mage notebook or project block files are available.
  - Manual actions remaining: implement in Mage and commit.

## Part D: RabbitMQ food-order stream

- [ ] D1. Routing table prediction — IMPLEMENTED (prediction template prepared)
  - Relevant files: stream/dispatcher.py, stream/driver.py
  - Evidence: scripts are ready for routing tests.
  - Manual actions remaining: run real RabbitMQ brokers to validate against the assignment pattern table.

- [ ] D2. Dispatcher and drivers — IMPLEMENTED
  - Relevant files: stream/dispatcher.py, stream/driver.py
  - Evidence: scripts handle topic exchange, routing, invalid-message NACK handling, and logging.
  - Manual actions remaining: start RabbitMQ and validate routing behaviour for two minutes.

- [ ] D3. ACK and NACK behaviour — IMPLEMENTED
  - Relevant files: stream/driver.py, stream/dispatcher.py
  - Evidence: invalid messages without a `zone` field are negatively acknowledged and good messages are acked.
  - Manual actions remaining: verify against a live broker instance.

## Part E: Report and viva

- [ ] E1. Final report PDF — BLOCKED
  - Relevant files: final PDF to be produced later.
  - Evidence: no report PDF or roll number/name is available yet.
  - Manual actions remaining: request roll no. and name, combine actual evidence, and export PDF.

- [ ] E2. Architecture diagram — BLOCKED
  - Evidence: not created yet.
  - Manual actions remaining: create diagram after service evidence is collected.

## Bonus: Stream into the lakehouse

- [ ] Bonus integration — BLOCKED
  - Relevant files: stream/
  - Evidence: no live Snowflake + RabbitMQ environment is available.
  - Manual actions remaining: set up environment and run the stream-to-gold end-to-end check.

## Testing evidence

- [ ] `python -m pytest -q` — TESTED
  - Evidence: 1 passed in 1.73s.
  - Relevant file: tests/test_prepare_data.py

- [ ] GitHub Actions CI workflow — VERIFIED locally only, not on GitHub
  - Relevant file: .github/workflows/ci.yml
  - Evidence: workflow file is present and ready to push.
  - Manual actions remaining: push to GitHub and trigger workflow.
