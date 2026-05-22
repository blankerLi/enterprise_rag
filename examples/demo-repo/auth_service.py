from __future__ import annotations


class AuthService:
    def __init__(self, users: dict[str, str]) -> None:
        self.users = users

    def login(self, username: str, password: str) -> bool:
        expected = self.users.get(username)
        return expected == password
