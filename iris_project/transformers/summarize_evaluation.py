if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


def summarize_evaluation_impl(evaluation):
    metrics = evaluation["metrics"]
    accuracy = float(metrics["accuracy"])

    if accuracy >= 0.90:
        performance = "excellent"
    elif accuracy >= 0.75:
        performance = "good"
    else:
        performance = "needs_improvement"

    return {
        "accuracy": accuracy,
        "performance": performance,
        "class_count": len(evaluation["labels"]),
        "confusion_matrix": evaluation["confusion_matrix"],
    }


@transformer
def summarize_evaluation(evaluation, **kwargs):
    return summarize_evaluation_impl(evaluation)


@test
def test_output(result):
    assert 0.0 <= result["accuracy"] <= 1.0
    assert result["class_count"] == 3
    assert result["performance"] in {
        "excellent", "good", "needs_improvement"
    }
    assert len(result["confusion_matrix"]) == 3
