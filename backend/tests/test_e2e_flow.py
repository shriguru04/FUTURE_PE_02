"""API-level end-to-end test of the main journey (no browser). Browser E2E is not included; see README."""
from tests.helpers import API


def test_full_journey(make_client):
    c = make_client()
    # register -> brand -> product -> campaign
    assert c.post(f"{API}/auth/register", json={"email": "e2e@example.com", "password": "journey-pass-1"}).status_code == 201
    brand = c.post(f"{API}/brands", json={"name": "GlowCo", "voice": "warm", "avoid_terms": ["guaranteed"]}).json()
    product = c.post(f"{API}/products", json={"brand_id": brand["id"], "name": "Glow Serum", "price": 24,
                                              "supported_claims": ["Fragrance-free"]}).json()
    campaign = c.post(f"{API}/campaigns", json={"name": "Autumn", "brand_id": brand["id"], "product_id": product["id"],
                                                "platform": "instagram_reels", "objective": "Drive trial"}).json()
    # generate (mock provider) -> edit -> save version
    assert c.post(f"{API}/campaigns/{campaign['id']}/generate", json={"num_hooks": 5}).status_code == 200
    r = c.patch(f"{API}/campaigns/{campaign['id']}/content", json={
        "platform": "instagram_reels", "section": "caption", "payload": {"text": "My edited caption"}})
    assert r.json()["current_version"] == 2
    versions = c.get(f"{API}/campaigns/{campaign['id']}/versions?section=caption").json()
    assert versions["total"] == 2
    # restore original, then export in every format
    original = next(v for v in versions["items"] if v["version_number"] == 1)
    assert c.post(f"{API}/campaigns/{campaign['id']}/versions/{original['id']}/restore").json()["current_version"] == 3
    for fmt in ("txt", "md", "json", "pdf"):
        e = c.post(f"{API}/campaigns/{campaign['id']}/export", json={"format": fmt})
        assert e.status_code == 200 and len(e.content) > 100
    # metrics + dashboard
    c.post(f"{API}/campaigns/{campaign['id']}/metrics", json={"metric_date": "2026-04-01", "impressions": 500, "clicks": 25})
    assert c.get(f"{API}/analytics/overview").json()["metrics"]["rates"]["ctr"] == 5.0
