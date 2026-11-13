# Iris pipeline preparation

The original course Mage project and Iris notebook were not supplied in this workspace. The Python modules in this folder are framework-independent implementations of the parts that can be built and tested locally; they are not represented as a verified Mage project or as the course's original block code.

## Local flow

```text
load_iris_frame -> prepare_data.transform -> train_model -> evaluate_model
                                                   \-> save_results
```

- `data.load_iris_frame()` loads scikit-learn's Iris frame.
- `transformers.prepare_data.transform()` assigns the deterministic 80/20 split required by the local pytest.
- `transformers.validate_data.validate_iris_data()` checks for missing values and exactly three classes.
- `transformers.train_model.train_model()` fits a deterministic decision tree using `max_depth`.
- `transformers.evaluate_model.evaluate_model()` returns a confusion matrix and weighted metrics.
- `exporters.save_results.save_results()` writes actual/predicted test labels to a CSV.

Run local tests from the repository root:

```bash
pytest -q
```

## Mage work still required

The assignment command is:

```bash
mage run iris_project iris_classifier --test
```

It has not been run because Mage and the course project are not present. The existing `pipelines/iris_classifier/metadata.yaml` is a scaffold and must be checked against the Mage version and original project before claiming that it is valid Mage metadata.

In the provided Mage project:

1. Connect the loader, preparation, training, and exporter blocks with their `@test` functions.
2. Run max depths 1 through 5 with `--runtime-vars`, deleting `iris_predictions.csv` before every run; record actual accuracy, test outcome, and output-file existence.
3. Add `evaluate_model` as a second downstream block of `train_model`, then record the actual confusion matrix and metrics.
4. Add and test the missing-values/three-classes block, and verify CI.

Do not treat local module tests as evidence that Mage executed or that any of its `@test` gates passed.
