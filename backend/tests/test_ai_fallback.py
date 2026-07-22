"""Tests for the offline business-analysis fallback."""

from app.services.ai_service import _call_openai


CONTEXT = """BUSINESS CONTEXT (as of 2026-07-22):
- Total Revenue: $5,955,818.00
- Total Orders: 277
- Total Customers: 20
- Total Products: 18
- This Month Revenue: $595,863.45

Top Products by Revenue:
  - Vertex ProBook 14: $1,000,000.00 (800 units)

Revenue by Region:
  - East: $1,400,000.00 (62 orders)

Low Stock Alerts:
  - 4K Conference Room Camera: stock=11, reorder_level=18
  - Electric Standing Desk: stock=7, reorder_level=10
"""


def test_ai_uses_local_evidence_when_api_key_is_missing(monkeypatch):
    monkeypatch.setattr("app.services.ai_service.settings.OPENAI_API_KEY", "")

    response = _call_openai("What inventory actions do you suggest?", CONTEXT)

    assert response.confidence == "high"
    assert response.short_answer.startswith("2 SKUs")
    assert len(response.data_evidence) == 2
    assert "external model" in response.reasoning
