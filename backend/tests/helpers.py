API = "/api/v1"


def mk_brand(c, name="Acme", **kw):
    r = c.post(f"{API}/brands", json={"name": name, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def mk_product(c, brand_id, name="Widget", **kw):
    r = c.post(f"{API}/products", json={"brand_id": brand_id, "name": name, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def mk_campaign(c, brand_id, product_id=None, name="Spring Launch", platform="instagram_reels", **kw):
    r = c.post(f"{API}/campaigns", json={"name": name, "brand_id": brand_id, "product_id": product_id,
                                         "platform": platform, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def world(c, **product_kw):
    b = mk_brand(c)
    p = mk_product(c, b["id"], **product_kw)
    camp = mk_campaign(c, b["id"], p["id"])
    return b, p, camp


def generate(c, campaign_id, **body):
    return c.post(f"{API}/campaigns/{campaign_id}/generate", json=body)
