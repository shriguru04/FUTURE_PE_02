from app.models import ContentVersion
from tests.helpers import API, generate, world


def _hooks(client, cid):
    return next(c for c in client.get(f"{API}/campaigns/{cid}/content").json() if c["section"] == "hooks")


def test_edit_creates_version_and_noop_does_not(client):
    _, _, camp = world(client)
    generate(client, camp["id"])
    patch = {"platform": "instagram_reels", "section": "hooks", "payload": {"items": ["Mine A", "Mine B"]}}
    r = client.patch(f"{API}/campaigns/{camp['id']}/content", json=patch)
    assert r.status_code == 200 and r.json()["current_version"] == 2
    assert _hooks(client, camp["id"])["payload"]["items"] == ["Mine A", "Mine B"]
    again = client.patch(f"{API}/campaigns/{camp['id']}/content", json=patch)
    assert again.json()["current_version"] == 2  # unchanged payload -> no noise version


def test_invalid_section_payloads_rejected(client):
    _, _, camp = world(client)
    generate(client, camp["id"])
    url = f"{API}/campaigns/{camp['id']}/content"
    assert client.patch(url, json={"platform": "instagram_reels", "section": "hooks", "payload": {"items": "x"}}).status_code == 422
    r = client.patch(url, json={"platform": "instagram_reels", "section": "primary_script", "payload": {"title": "t"}})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_section_payload"
    assert client.patch(url, json={"platform": "instagram_reels", "section": "bogus", "payload": {}}).status_code == 422


def test_restore_appends_new_version_and_preserves_history(client, db):
    _, _, camp = world(client)
    generate(client, camp["id"])
    url = f"{API}/campaigns/{camp['id']}/content"
    original = _hooks(client, camp["id"])["payload"]
    client.patch(url, json={"platform": "instagram_reels", "section": "hooks", "payload": {"items": ["Edited"]}})
    versions = client.get(f"{API}/campaigns/{camp['id']}/versions?section=hooks").json()["items"]
    assert len(versions) == 2
    v1 = next(v for v in versions if v["version_number"] == 1)
    r = client.post(f"{API}/campaigns/{camp['id']}/versions/{v1['id']}/restore")
    assert r.status_code == 200 and r.json()["current_version"] == 3
    assert r.json()["payload"] == original
    after = client.get(f"{API}/campaigns/{camp['id']}/versions?section=hooks").json()["items"]
    assert len(after) == 3  # nothing deleted
    assert next(v for v in after if v["version_number"] == 3)["source"] == "restore"
    assert db.query(ContentVersion).filter_by(version_number=1).count() >= 1


def test_restore_unknown_version_404(client):
    _, _, camp = world(client)
    r = client.post(f"{API}/campaigns/{camp['id']}/versions/00000000-0000-0000-0000-000000000000/restore")
    assert r.status_code == 404


def test_hashtags_are_normalised_on_edit(client):
    _, _, camp = world(client)
    generate(client, camp["id"])
    r = client.patch(f"{API}/campaigns/{camp['id']}/content", json={
        "platform": "instagram_reels", "section": "hashtags", "payload": {"items": ["Fun Stuff", "#fun stuff", "tips!"]}})
    assert r.json()["payload"]["items"] == ["#FunStuff", "#tips"]
