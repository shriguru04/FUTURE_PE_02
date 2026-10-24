import pytest

from app.ai.base import ProviderNotConfigured
from app.ai.factory import build_provider
from app.core.config import Settings
from app.models import CampaignContent, ContentVersion, GenerationJob
from tests.helpers import API, generate, mk_brand, mk_campaign, mk_product, world


def test_generate_persists_full_pack_and_flags_mock(client, provider, db):
    b, p, camp = world(client)
    r = generate(client, camp["id"], num_hooks=6, num_variations=2)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_mock"] is True and body["results"][0]["status"] == "succeeded"
    content = {c["section"]: c for c in client.get(f"{API}/campaigns/{camp['id']}/content").json()}
    assert set(content) == {"summary", "hooks", "primary_script", "alt_scripts", "caption", "ctas", "hashtags",
                            "variations", "adaptation", "claims_review"}
    assert len(content["hooks"]["payload"]["items"]) == 6
    assert len(content["variations"]["payload"]["items"]) == 2
    assert content["summary"]["payload"]["text"].startswith("[MOCK PROVIDER OUTPUT]")
    assert content["hooks"]["current_version"] == 1
    assert client.get(f"{API}/campaigns/{camp['id']}").json()["status"] == "in_progress"
    assert db.query(GenerationJob).filter_by(status="succeeded").count() == 1


def test_regenerating_creates_new_versions_not_overwrites(client):
    _, _, camp = world(client)
    generate(client, camp["id"])
    generate(client, camp["id"])
    v = client.get(f"{API}/campaigns/{camp['id']}/versions?section=hooks").json()
    assert v["total"] == 2 and sorted(i["version_number"] for i in v["items"]) == [1, 2]


def test_multi_platform_generation(client):
    _, _, camp = world(client)
    r = generate(client, camp["id"], platforms=["tiktok", "youtube_shorts", "tiktok"])
    assert [x["platform"] for x in r.json()["results"]] == ["tiktok", "youtube_shorts"]
    assert len(client.get(f"{API}/campaigns/{camp['id']}/content?platform=tiktok").json()) == 10
    assert len(client.get(f"{API}/campaigns/{camp['id']}/content").json()) == 20


def test_malformed_output_is_retried_then_succeeds(client, provider):
    _, _, camp = world(client)
    provider.script = ["malformed", "wrong_schema", "ok"]
    assert generate(client, camp["id"]).status_code == 200
    assert provider.calls == 3


def test_persistently_invalid_output_fails_safely(client, provider, db):
    _, _, camp = world(client)
    provider.script = ["wrong_schema"]
    r = generate(client, camp["id"])
    assert r.status_code == 502 and r.json()["error"]["code"] == "invalid_output"
    assert provider.calls == 3  # 1 try + 2 bounded retries
    assert client.get(f"{API}/campaigns/{camp['id']}/content").json() == []  # nothing fabricated or saved
    job = db.query(GenerationJob).one()
    assert job.status == "failed" and job.error_code == "invalid_output"


def test_transient_provider_error_retries(client, provider):
    _, _, camp = world(client)
    provider.script = ["error", "error", "ok"]
    assert generate(client, camp["id"]).status_code == 200 and provider.calls == 3


def test_provider_failure_is_reported_not_hidden(client, provider):
    _, _, camp = world(client)
    provider.script = ["error"]
    r = generate(client, camp["id"])
    assert r.status_code == 502 and r.json()["error"]["code"] == "provider_unavailable"
    assert provider.calls == 3
    provider.calls, provider.script = 0, ["fatal"]
    r = generate(client, camp["id"])
    assert r.json()["error"]["code"] == "provider_auth" and provider.calls == 1  # non-retryable


def test_request_validation(client):
    _, _, camp = world(client)
    for bad in ({"platforms": ["myspace"]}, {"num_hooks": 0}, {"num_hooks": 11}, {"duration_seconds": 1},
                {"reference_content": "x" * 5001}, {"content_format": "nope"}, {"platforms": []}):
        assert generate(client, camp["id"], **bad).status_code == 422, bad


def test_avoid_terms_and_unsupported_claims_are_flagged(client):
    b = mk_brand(client, "Mop Co", avoid_terms=["miracle"])
    p = mk_product(client, b["id"], name="Miracle Mop", supported_claims=["Machine washable head"])
    camp = mk_campaign(client, b["id"], p["id"])
    generate(client, camp["id"])
    items = next(c for c in client.get(f"{API}/campaigns/{camp['id']}/content").json()
                 if c["section"] == "claims_review")["payload"]["items"]
    assert any(i["status"] == "unsupported" and "miracle" in i["claim"].lower() for i in items)


def test_regenerate_single_section(client):
    _, _, camp = world(client)
    generate(client, camp["id"])
    r = client.post(f"{API}/campaigns/{camp['id']}/regenerate-section",
                    json={"platform": "instagram_reels", "section": "hooks", "instruction": "funnier"})
    assert r.status_code == 200
    v = client.get(f"{API}/campaigns/{camp['id']}/versions?section=hooks").json()["items"]
    assert {i["source"] for i in v} == {"generation", "section_regeneration"}
    caption = client.get(f"{API}/campaigns/{camp['id']}/versions?section=caption").json()
    assert caption["total"] == 1  # untouched sections keep a single version


def test_provider_factory_rules():
    with pytest.raises(ProviderNotConfigured):
        build_provider(Settings(llm_provider="openai_compat", llm_api_key="", _env_file=None))
    with pytest.raises(ProviderNotConfigured):
        build_provider(Settings(llm_provider="mock", app_env="production", _env_file=None))
    p = build_provider(Settings(llm_provider="openai_compat", llm_api_key="k", llm_base_url="https://api.x.ai/v1",
                                llm_model="grok-4", _env_file=None))
    assert p.base_url == "https://api.x.ai/v1" and p.model == "grok-4"
    assert build_provider(Settings(llm_provider="openai_compat", llm_base_url="http://localhost:11434/v1",
                                   _env_file=None)).name == "openai_compat"
