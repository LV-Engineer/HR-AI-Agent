from starlette.requests import Request

from app.core.rate_limit import rate_limit_key
from app.core.security import create_access_token

def _make_request(headers: dict[str, str]) -> Request:
    scope = {
        'type': 'http',
        'headers': [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        'client': ('127.0.0.1', 12345),
    }
    return Request(scope)

class TestLoginRateLimit:
    def test_login_rate_limited_after_five_attempts(self, client) -> None:
        payload = {'email': 'nobody.nowhere@hirelume.dev', 'password': 'wrong'}

        for _ in range(5):
            response = client.post('/auth/login', json=payload)
            assert response.status_code == 401

        response = client.post('/auth/login', json=payload)

        assert response.status_code == 429

class TestRateLimitKey:
    def test_uses_user_id_for_valid_token(self) -> None:
        token = create_access_token('user-123')
        request = _make_request({'Authorization': f'Bearer {token}'})

        assert rate_limit_key(request) == 'user:user-123'

    def test_falls_back_to_ip_for_invalid_token(self) -> None:
        request = _make_request({'Authorization': 'Bearer not-a-real-token'})

        assert rate_limit_key(request) == '127.0.0.1'

    def test_falls_back_to_ip_when_no_auth_header(self) -> None:
        request = _make_request({})

        assert rate_limit_key(request) == '127.0.0.1'
