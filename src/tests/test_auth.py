from app.auth import Authentication, SECRET_KEY, ALGORITHM, users
import pytest
import jwt


@pytest.mark.parametrize('login, password', [
    pytest.param('mike', 'superboss', id='is correct'),
    # pytest.param('', 'superboss', id='is not correct', marks=pytest.mark.xfail()),
    # pytest.param('mike', '', id='is not correct', marks=pytest.mark.xfail()),
    # pytest.param('', '', id='is not correct', marks=pytest.mark.xfail()),
])
def test_registration(login, password):
    Authentication().registration(login, password)
    token = jwt.encode({'user_login': login, 'password': password}, SECRET_KEY, ALGORITHM)
    assert users[login] == token

@pytest.mark.parametrize('login, password', [
    pytest.param('mike', 'superboss', id='is correct'),
    # pytest.param('', 'superboss', id='is not correct', marks=pytest.mark.xfail()),
    # pytest.param('mike', '', id='is not correct', marks=pytest.mark.xfail()),
    # pytest.param('', '', id='is not correct', marks=pytest.mark.xfail()),
    # pytest.param('johny', 'pwd123', id='is not correct', marks=pytest.mark.xfail()),
])
def test_authorisation(login, password):
    Authentication().registration('mike', 'superboss')
    token = jwt.encode({'user_login': login, 'password': password}, SECRET_KEY, ALGORITHM)
    assert Authentication().authorisation(login, password) == token



