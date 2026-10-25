def test_intentionally_failed_gate_demonstration():
    """Controlled Lab 5 probe: this branch must never be merged."""
    assert False, "Intentional CI failure to verify protected main"
