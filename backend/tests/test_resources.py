from tests.helpers import API, mk_brand, mk_campaign, mk_product, world


def test_brand_crud(client):
    b = mk_brand(client, "Acme", avoid_terms=["cure"], website_url="https://acme.test")
    assert client.get(f"{API}/brands/{b['id']}").json()["avoid_terms"] == ["cure"]
    r = client.patch(f"{API}/brands/{b['id']}", json={"voice": "friendly"})
    assert r.status_code == 200 and r.json()["voice"] == "friendly" and r.json()["name"] == "Acme"
    assert client.post(f"{API}/brands", json={"name": "Acme"}).status_code == 409
    assert client.post(f"{API}/brands", json={"name": ""}).status_code == 422
    assert client.post(f"{API}/brands", json={"name": "B", "website_url": "ftp://x"}).status_code == 422
    assert client.patch(f"{API}/brands/{b['id']}", json={"name": None}).status_code == 422
    assert client.get(f"{API}/brands?q=ac").json()["total"] == 1
    assert client.get(f"{API}/brands?q=zzz").json()["total"] == 0
    assert client.delete(f"{API}/brands/{b['id']}").status_code == 204
    assert client.get(f"{API}/brands/{b['id']}").status_code == 404


def test_product_crud_and_brand_delete_cascade(client):
    b = mk_brand(client)
    p = mk_product(client, b["id"], price=19.5, supported_claims=["Machine washable"])
    assert p["price"] == 19.5
    assert client.patch(f"{API}/products/{p['id']}", json={"price": -1}).status_code == 422
    assert client.post(f"{API}/products", json={"brand_id": b["id"], "name": "Widget"}).status_code == 409
    assert client.get(f"{API}/products?brand_id={b['id']}").json()["total"] == 1
    assert client.delete(f"{API}/brands/{b['id']}").status_code == 204
    assert client.get(f"{API}/products/{p['id']}").status_code == 404


def test_campaign_crud_filters_and_validation(client):
    b = mk_brand(client)
    p = mk_product(client, b["id"])
    c1 = mk_campaign(client, b["id"], p["id"], name="Spring Sale", platform="tiktok")
    mk_campaign(client, b["id"], None, name="Winter", platform="youtube_shorts")
    assert client.get(f"{API}/campaigns?q=spring").json()["total"] == 1
    assert client.get(f"{API}/campaigns?platform=tiktok").json()["total"] == 1
    assert client.get(f"{API}/campaigns?status=draft").json()["total"] == 2
    assert client.get(f"{API}/campaigns?status=bogus").status_code == 422
    assert client.get(f"{API}/campaigns?page_size=1").json()["items"].__len__() == 1
    assert client.post(f"{API}/campaigns", json={"name": "x", "brand_id": b["id"], "platform": "myspace"}).status_code == 422
    r = client.patch(f"{API}/campaigns/{c1['id']}", json={"status": "approved", "notes": "ok"})
    assert r.json()["status"] == "approved"
    assert client.patch(f"{API}/campaigns/{c1['id']}", json={"status": "nope"}).status_code == 422
    assert client.delete(f"{API}/campaigns/{c1['id']}").status_code == 204


def test_brand_with_campaigns_cannot_be_deleted_and_product_delete_keeps_campaign(client):
    b, p, camp = world(client)
    assert client.delete(f"{API}/brands/{b['id']}").status_code == 409
    assert client.delete(f"{API}/products/{p['id']}").status_code == 204
    assert client.get(f"{API}/campaigns/{camp['id']}").json()["product_id"] is None


def test_product_must_belong_to_campaign_brand(client):
    b1, b2 = mk_brand(client, "One"), mk_brand(client, "Two")
    p2 = mk_product(client, b2["id"])
    r = client.post(f"{API}/campaigns", json={"name": "x", "brand_id": b1["id"], "product_id": p2["id"],
                                              "platform": "tiktok"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "product_brand_mismatch"


def test_duplicate_campaign_copies_content(client):
    b, p, camp = world(client)
    assert client.post(f"{API}/campaigns/{camp['id']}/generate", json={}).status_code == 200
    d = client.post(f"{API}/campaigns/{camp['id']}/duplicate")
    assert d.status_code == 201 and d.json()["name"].endswith("(copy)") and d.json()["status"] == "draft"
    assert len(client.get(f"{API}/campaigns/{d.json()['id']}/content").json()) == 10


def test_user_isolation_everywhere(client, other):
    b, p, camp = world(client)
    client.post(f"{API}/campaigns/{camp['id']}/generate", json={})
    versions = client.get(f"{API}/campaigns/{camp['id']}/versions").json()["items"]
    vid = versions[0]["id"]
    cid = camp["id"]
    probes = [
        ("get", f"{API}/brands/{b['id']}", None), ("patch", f"{API}/brands/{b['id']}", {"voice": "x"}),
        ("delete", f"{API}/brands/{b['id']}", None), ("get", f"{API}/products/{p['id']}", None),
        ("patch", f"{API}/products/{p['id']}", {"cta": "x"}), ("delete", f"{API}/products/{p['id']}", None),
        ("get", f"{API}/campaigns/{cid}", None), ("patch", f"{API}/campaigns/{cid}", {"notes": "x"}),
        ("delete", f"{API}/campaigns/{cid}", None), ("post", f"{API}/campaigns/{cid}/duplicate", None),
        ("post", f"{API}/campaigns/{cid}/generate", {}),
        ("post", f"{API}/campaigns/{cid}/regenerate-section", {"platform": "tiktok", "section": "hooks"}),
        ("get", f"{API}/campaigns/{cid}/content", None),
        ("patch", f"{API}/campaigns/{cid}/content", {"platform": "instagram_reels", "section": "caption", "payload": {"text": "x"}}),
        ("get", f"{API}/campaigns/{cid}/versions", None), ("post", f"{API}/campaigns/{cid}/versions/{vid}/restore", None),
        ("post", f"{API}/campaigns/{cid}/export", {"format": "txt"}),
        ("get", f"{API}/campaigns/{cid}/analytics", None),
        ("post", f"{API}/campaigns/{cid}/metrics", {"metric_date": "2026-01-01", "clicks": 1}),
    ]
    for method, url, body in probes:
        r = getattr(other, method)(url, **({"json": body} if body is not None else {}))
        assert r.status_code == 404, (method, url, r.status_code)
    assert other.get(f"{API}/brands").json()["total"] == 0
    assert other.get(f"{API}/campaigns").json()["total"] == 0
    # cannot attach someone else's brand/product to your own campaign
    assert other.post(f"{API}/campaigns", json={"name": "x", "brand_id": b["id"], "platform": "tiktok"}).status_code == 404
    ob = mk_brand(other, "Mine")
    assert other.post(f"{API}/campaigns", json={"name": "x", "brand_id": ob["id"], "product_id": p["id"],
                                                "platform": "tiktok"}).status_code == 404
    # owner's data untouched
    assert client.get(f"{API}/campaigns/{cid}").status_code == 200
