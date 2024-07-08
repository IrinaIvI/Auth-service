from app.auth import Authentication, users, SECRET_KEY, ALGORITHM
import pytest
import jwt


@pytest.mark.parametrize('login, password', [
    pytest.param('mike', 'superboss', id='is correct')
])
def test_registration(login, password):
    token = jwt.encode({'user_login': login, 'password': password}, SECRET_KEY, ALGORITHM)
    assert Authentication().registration(login, password) == token

def test_authorisation():
    pass
