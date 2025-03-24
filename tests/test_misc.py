from copy import deepcopy

from pysatl_experiment.misc import deep_merge_dicts


def test_deep_merge_dicts():
    a = {"first": {"rows": {"pass": "dog", "number": "1", "test": None}}}
    b = {"first": {"rows": {"fail": "cat", "number": "5", "test": "asdf"}}}
    res = {"first": {"rows": {"pass": "dog", "fail": "cat", "number": "5", "test": "asdf"}}}
    res2 = {"first": {"rows": {"pass": "dog", "fail": "cat", "number": "1", "test": None}}}
    assert deep_merge_dicts(b, deepcopy(a)) == res

    assert deep_merge_dicts(a, deepcopy(b)) == res2

    res2["first"]["rows"]["test"] = "asdf"
    assert deep_merge_dicts(a, deepcopy(b), allow_null_overrides=False) == res2
