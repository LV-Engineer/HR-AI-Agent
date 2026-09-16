class TestLogin:
    def test_login_success(self, client, test_user):
        email, password = test_user

        response = client.post('/auth/login', json={'email': email, 'password': password})

        assert response.status_code == 200
        body = response.json()
        assert 'access_token' in body
        assert 'refresh_token' in body

    def test_login_wrong_password(self, client):
        response = client.post('/auth/login', json={'email': 'test.user@hirelume.dev', 'password': 'wrong'})

        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        response = client.post('/auth/login', json={'email': 'nobody.nowhere@hirelume.dev', 'password': 'password123'})

        assert response.status_code == 401

    def test_login_malformed_email_rejected(self, client):
        response = client.post('/auth/login', json={'email': 'not-a-valid-email', 'password': 'password123'})

        assert response.status_code == 422
