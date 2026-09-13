from sqlalchemy import text

def _login(client, email, password):
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return response.json()

def test_me_with_valid_token(client, test_user):
    email, password = test_user
    tokens = _login(client, email, password)

    response = client.get('/auth/me', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

    assert response.status_code == 200
    assert response.json()['email'] == email

def test_me_missing_token(client):
    response = client.get('/auth/me')

    assert response.status_code == 401

def test_me_invalid_token(client):
    response = client.get('/auth/me', headers={'Authorization': 'Bearer not-a-real-token'})

    assert response.status_code == 401

def test_logout_revokes_refresh_token(client, test_user):
    email, password = test_user
    tokens = _login(client, email, password)

    response = client.post('/auth/logout', json={'refresh_token': tokens['refresh_token']})
    assert response.status_code == 204

    reused = client.post('/auth/refresh', json={'refresh_token': tokens['refresh_token']})
    assert reused.status_code == 401

def test_me_deleted_user(client, db_session, test_user):
    email, password = test_user
    tokens = _login(client, email, password)

    db_session.execute(text('DELETE FROM auth.users WHERE email = :email'), {'email': email})
    db_session.commit()

    response = client.get('/auth/me', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'User no longer exists'