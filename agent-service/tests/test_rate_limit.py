def test_login_rate_limited_after_five_attempts(client):
    payload = {'email': 'nobody.nowhere@hirelume.dev', 'password': 'wrong'}

    for _ in range(5):
        response = client.post('/auth/login', json=payload)
        assert response.status_code == 401

    response = client.post('/auth/login', json=payload)

    assert response.status_code == 429