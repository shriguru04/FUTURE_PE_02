import datetime as dt
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Brand, Campaign, CampaignContent, CampaignMetric, User


def _user(db, email="u@example.com"):
    u = User(email=email, password_hash="x")
    db.add(u)
    db.commit()
    return u


def _campaign(db, u):
    b = Brand(user_id=u.id, name="B")
    db.add(b)
    db.flush()
    c = Campaign(user_id=u.id, brand_id=b.id, name="C", platform="tiktok")
    db.add(c)
    db.commit()
    return b, c


def test_negative_metric_rejected(db):
    u = _user(db)
    _, c = _campaign(db, u)
    db.add(CampaignMetric(user_id=u.id, campaign_id=c.id, metric_date=dt.date(2026, 1, 1), clicks=-5))
    with pytest.raises(IntegrityError):
        db.commit()


def test_invalid_platform_and_status_rejected(db):
    u = _user(db)
    b, _ = _campaign(db, u)
    db.rollback()
    db.add(Campaign(user_id=u.id, brand_id=b.id, name="bad", platform="myspace"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(Campaign(user_id=u.id, brand_id=b.id, name="bad", platform="tiktok", status="weird"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_unique_brand_name_per_user_but_not_across_users(db):
    u1, u2 = _user(db, "a@example.com"), _user(db, "b@example.com")
    db.add_all([Brand(user_id=u1.id, name="Same"), Brand(user_id=u2.id, name="Same")])
    db.commit()
    db.add(Brand(user_id=u1.id, name="Same"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_cascade_and_restrict(db):
    u = _user(db)
    b, c = _campaign(db, u)
    db.add(CampaignContent(user_id=u.id, campaign_id=c.id, platform="tiktok", section="hooks", payload={"items": []}))
    db.commit()
    db.delete(b)
    with pytest.raises(IntegrityError):  # brand has campaigns -> RESTRICT
        db.commit()
    db.rollback()
    db.delete(c)
    db.commit()
    assert db.query(CampaignContent).count() == 0  # content removed with campaign


def test_foreign_key_enforced(db):
    db.add(Brand(user_id=uuid.uuid4(), name="orphan"))
    with pytest.raises(IntegrityError):
        db.commit()
