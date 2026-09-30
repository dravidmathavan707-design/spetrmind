from evaluation.temporal_split import temporal_split


def test_temporal_split_preserves_time_order():
    rows = [{"time": i} for i in range(10)]
    split = temporal_split(rows, train_fraction=0.6, validation_fraction=0.2)

    assert len(split["train"]) == 6
    assert len(split["validation"]) == 2
    assert len(split["test"]) == 2
    assert split["train"][0]["time"] == 0
    assert split["test"][-1]["time"] == 9
