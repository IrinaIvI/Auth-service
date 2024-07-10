from app.auth import Authentication, SECRET_KEY, ALGORITHM, users
import pytest
import jwt


@pytest.mark.parametrize('login, password', [
    pytest.param('mike', 'superboss', id='is correct')
])
def test_registration(login, password):
    Authentication().registration(login, password)
    token = jwt.encode({'user_login': login, 'password': password}, SECRET_KEY, ALGORITHM)
    assert users[login] == token

@pytest.mark.parametrize('login, password', [
    pytest.param('mike', 'superboss', id='is correct'),
    pytest.param('', 'superboss', id='is not correct'),
    pytest.param('mike', '', id='is not correct'),
    pytest.param('mike', 'superboss', id='is correct'),
    pytest.param('', '', id='is correct'),
])
def test_authorisation(login, password):
    Authentication().registration(login, password)
    token = jwt.encode({'user_login': login, 'password': password}, SECRET_KEY, ALGORITHM)
    assert Authentication().authorisation(login, password) == token



