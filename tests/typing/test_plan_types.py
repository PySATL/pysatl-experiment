"""Static checks for extension plans and planner/factory compatibility."""

from pathlib import Path

from mypy import api


def test_registration_checks_custom_plan_type(tmp_path):
    source = Path(__file__).with_name("plan_registration.py").read_text()
    module = tmp_path / "extension.py"
    module.write_text(source)
    args = ["--follow-imports=silent", "--cache-dir", str(tmp_path / "cache"), str(module)]
    stdout, stderr, status = api.run(args)
    assert status == 0, stdout + stderr

    module.write_text(source.replace("task_planner=plan,", "task_planner=wrong_plan,"))
    stdout, stderr, status = api.run(args)
    assert status == 1, stdout + stderr
    assert 'type parameter "PlanT"' in stdout

    module.write_text(source.replace("execution=[42]", 'execution=["wrong task"]'))
    stdout, stderr, status = api.run(args)
    assert status == 1, stdout + stderr
    assert "list-item" in stdout


def test_factory_checks_generation_task_type(tmp_path):
    source = (Path(__file__).parents[1] / "experiment_execution/experiment_factory/test_custom_generation_factory.py").read_text()
    module = tmp_path / "generation_extension.py"
    module.write_text(source)
    args = ["--follow-imports=silent", "--cache-dir", str(tmp_path / "cache"), str(module)]
    stdout, stderr, status = api.run(args)
    assert status == 0, stdout + stderr

    module.write_text(
        source.replace("tasks: list[str]) -> CustomGenerationStep:", "tasks: list[int]) -> CustomGenerationStep:")
    )
    stdout, stderr, status = api.run(args)
    assert status == 1, stdout + stderr
    assert "override" in stdout
