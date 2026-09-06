"""UI smoke test: the Streamlit app must boot and the copilot must answer."""
import pytest

st = pytest.importorskip("streamlit")


def test_streamlit_app_boots_and_answers():
    import os
    from streamlit.testing.v1 import AppTest
    app_path = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "app.py")
    at = AppTest.from_file(app_path, default_timeout=90)
    at.run()
    assert not at.exception
    ask = [b for b in at.button if "Ask TripPilot" in b.label]
    assert ask, "copilot primary button missing"
    ask[0].click().run()
    assert not at.exception
    labels = [m.label for m in at.metric]
    assert "Judge" in labels and "Latency" in labels
