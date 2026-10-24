import pytest

from tests.helpers import API, generate, world


@pytest.mark.parametrize("fmt,ctype,magic", [("txt", "text/plain", b"SPRING LAUNCH"), ("md", "text/markdown", b"# Spring Launch"),
                                             ("json", "application/json", b'"campaign"'), ("pdf", "application/pdf", b"%PDF")])
def test_export_formats(client, fmt, ctype, magic):
    _, _, camp = world(client)
    generate(client, camp["id"])
    r = client.post(f"{API}/campaigns/{camp['id']}/export", json={"format": fmt})
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith(ctype)
    assert f'filename="spring-launch-' in r.headers["content-disposition"] and r.headers["content-disposition"].endswith(f'.{fmt}"')
    assert magic in r.content[:400] or magic in r.content


def test_export_without_content_and_bad_format(client):
    _, _, camp = world(client)
    assert client.post(f"{API}/campaigns/{camp['id']}/export", json={"format": "txt"}).status_code == 409
    assert client.post(f"{API}/campaigns/{camp['id']}/export", json={"format": "docx"}).status_code == 422


def test_export_platform_filter_and_review_notes(client):
    _, _, camp = world(client)
    generate(client, camp["id"], platforms=["tiktok", "youtube_shorts"])
    r = client.post(f"{API}/campaigns/{camp['id']}/export", json={"format": "md", "platforms": ["tiktok"]})
    assert "Tiktok" in r.text and "Youtube Shorts" not in r.text
    assert "Pre-publication review checklist" in r.text and "Factual-claims review" in r.text


def test_export_is_owner_only(client, other):
    _, _, camp = world(client)
    generate(client, camp["id"])
    assert other.post(f"{API}/campaigns/{camp['id']}/export", json={"format": "json"}).status_code == 404
