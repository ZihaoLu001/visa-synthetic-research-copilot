from fastapi.testclient import TestClient

from api import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_run_endpoint_returns_summary_payload():
    client = TestClient(app)
    response = client.post(
        "/run",
        json={
            "survey_text": "How relevant is this value proposition for your payment needs?\nWhat annual fee in CHF feels acceptable?",
            "micro_population_n": 6,
            "consistency_runs": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_count"] > 0
    assert payload["questions"]
    assert payload["aggregate"]["runtime"]["provider_independent"] is True
    assert payload["aggregate"]["provider"] in {"mock", "watsonx"}
    assert payload["aggregate"]["model_id"]
    assert payload["aggregate"]["decision_brief"]["consultant_quality_layer"]["decision_risk"]
    assert payload["aggregate"]["decision_brief"]["synthetic_customer_lens"]["synthetic_customer_board"]
    assert payload["aggregate"]["decision_brief"]["synthetic_customer_lens"]["real_customer_bridge"]
    assert "overall" in payload["validation"]
