from viu_media.cli.service.auth.service import AuthService
from viu_media.libs.media_api.types import UserProfile


def test_load_auth_creates_file_when_missing(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    monkeypatch.setattr("viu_media.cli.service.auth.service.AUTH_FILE", auth_file)

    service = AuthService(media_api="anilist")
    profile = service.get_auth()

    assert profile is None
    assert auth_file.exists()


def test_save_and_get_auth_roundtrip(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    monkeypatch.setattr("viu_media.cli.service.auth.service.AUTH_FILE", auth_file)

    service = AuthService(media_api="anilist")
    user = UserProfile(id=1, name="test-user", avatar_url="https://img/avatar.png")

    service.save_user_profile(user, "token-abc")
    auth = service.get_auth()

    assert auth is not None
    assert auth.token == "token-abc"
    assert auth.user_profile.name == "test-user"


def test_clear_user_profile_deletes_auth_file(tmp_path, monkeypatch):
    auth_file = tmp_path / "auth.json"
    monkeypatch.setattr("viu_media.cli.service.auth.service.AUTH_FILE", auth_file)

    service = AuthService(media_api="anilist")
    user = UserProfile(id=2, name="clear-me")
    service.save_user_profile(user, "token")
    assert auth_file.exists()

    service.clear_user_profile()

    assert not auth_file.exists()
