from policy_forge.data import fetch, policy_text


def test_fetch_airline():
    path = fetch("airline")
    assert path.exists()
    assert path.suffix == ".md"


def test_policy_text():
    text = policy_text("airline")
    assert "Airline Agent Policy" in text
    assert len(text) > 1000
