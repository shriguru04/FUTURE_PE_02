from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address, enabled=get_settings().rate_limit_enabled, headers_enabled=False)


def auth_limit(*_args) -> str:
    return get_settings().rate_limit_auth


def generate_limit(*_args) -> str:
    return get_settings().rate_limit_generate
