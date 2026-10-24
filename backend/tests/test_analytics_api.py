from tests.helpers import API, world


def test_metrics_flow_and_rates(client):
    _, _, camp = world(client)
    url = f"{API}/campaigns/{camp['id']}/metrics"
    r = client.post(url, json={"metric_date": "2026-03-01", "impressions": 1000, "clicks": 50, "conversions": 5,
                               "spend": 100, "revenue": 300})
    assert r.status_code == 201
    row = r.json()
    assert row["ctr"] == 5.0 and row["conversion_rate"] == 10.0 and row["cpc"] == 2.0 and row["cpa"] == 20.0 and row["roas"] == 3.0
    client.post(url, json={"metric_date": "2026-03-02", "impressions": 1000, "clicks": 0, "spend": 10})
    a = client.get(f"{API}/campaigns/{camp['id']}/analytics").json()
    assert a["data_source"] == "manual_entry" and a["row_count"] == 2
    assert a["totals"]["impressions"] == 2000 and a["totals"]["revenue"] == 300.0
    assert a["rates"]["ctr"] == 2.5
    assert a["rows"][1]["cpc"] is None and a["rows"][1]["conversion_rate"] is None  # zero clicks -> n/a, not 0
    assert "not connected" in a["disclaimer"] or "not " in a["disclaimer"]


def test_metric_validation_and_duplicates(client):
    _, _, camp = world(client)
    url = f"{API}/campaigns/{camp['id']}/metrics"
    assert client.post(url, json={"metric_date": "2026-03-01"}).status_code == 422
    assert client.post(url, json={"metric_date": "2026-03-01", "clicks": -1}).status_code == 422
    assert client.post(url, json={"metric_date": "2026-03-01", "impressions": 5, "clicks": 9}).status_code == 422
    assert client.post(url, json={"metric_date": "2026-03-01", "clicks": 3}).status_code == 201
    assert client.post(url, json={"metric_date": "2026-03-01", "clicks": 4}).status_code == 409


def test_overview_with_and_without_data(client):
    r = client.get(f"{API}/analytics/overview").json()
    assert r["campaign_counts"]["total"] == 0 and r["metrics"]["has_data"] is False
    assert r["metrics"]["rates"]["ctr"] is None
    _, _, camp = world(client)
    client.post(f"{API}/campaigns/{camp['id']}/generate", json={})
    client.post(f"{API}/campaigns/{camp['id']}/metrics", json={"metric_date": "2026-03-01", "impressions": 200, "clicks": 10})
    r = client.get(f"{API}/analytics/overview").json()
    assert r["campaign_counts"]["by_status"] == {"in_progress": 1}
    assert r["platform_distribution"] == {"instagram_reels": 1}
    assert r["metrics"]["has_data"] and r["metrics"]["rates"]["ctr"] == 5.0
    assert r["metrics"]["totals"]["spend"] is None and r["metrics"]["rates"]["cpc"] is None
    assert len(r["recent_generations"]) == 1 and len(r["recent_campaigns"]) == 1


def test_delete_metric_and_isolation(client, other):
    _, _, camp = world(client)
    m = client.post(f"{API}/campaigns/{camp['id']}/metrics", json={"metric_date": "2026-03-01", "clicks": 1}).json()
    assert other.delete(f"{API}/campaigns/{camp['id']}/metrics/{m['id']}").status_code == 404
    assert client.delete(f"{API}/campaigns/{camp['id']}/metrics/{m['id']}").status_code == 204
    assert other.get(f"{API}/analytics/overview").json()["metrics"]["has_data"] is False
