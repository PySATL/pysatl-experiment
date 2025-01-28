from stattest.experiment.listener.listeners import TimeEstimationListener


def test_time_estimation_before():
    listener = TimeEstimationListener()
    listener.before()
    assert listener.start_time is not None


def test_time_estimation_after():
    listener = TimeEstimationListener()
    listener.before()
    listener.after()
    assert listener.start_time is not None
    assert listener.end_time is not None
