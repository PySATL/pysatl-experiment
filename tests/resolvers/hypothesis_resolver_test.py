from stattest.resolvers.hypothesis_resolver import HypothesisResolver


def test_cauchy_rvs_generator():
    hypothesis = HypothesisResolver.load_hypothesis("NormalHypothesis")
    assert hypothesis is not None
