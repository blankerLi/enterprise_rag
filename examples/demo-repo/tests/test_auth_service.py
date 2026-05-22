from auth_service import AuthService


def test_login_success() -> None:
    service = AuthService({"alice": "secret"})
    assert service.login("alice", "secret") is True


def test_login_failure() -> None:
    service = AuthService({"alice": "secret"})
    assert service.login("alice", "wrong") is False
