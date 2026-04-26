import json
import logging
from pathlib import Path
from typing import Optional

from ....core.constants import APP_DATA_DIR
from ....core.utils.file import AtomicWriter, FileLock
from ....libs.media_api.types import UserProfile
from .model import AuthModel, AuthProfile

logger = logging.getLogger(__name__)

AUTH_FILE = APP_DATA_DIR / "auth.json"


class AuthService:
    def __init__(self, media_api: str, auth_file: Path | None = None):
        self.path = auth_file or AUTH_FILE
        self.media_api = media_api
        _lock_file = self.path.with_suffix(".lock")
        self._lock = FileLock(_lock_file)

    def get_auth(self) -> Optional[AuthProfile]:
        auth = self._load_auth()
        return auth.profiles.get(self.media_api)

    def save_user_profile(self, profile: UserProfile, token: str) -> None:
        auth = self._load_auth()
        auth.profiles[self.media_api] = AuthProfile(user_profile=profile, token=token)
        self._save_auth(auth)
        logger.info(f"Successfully saved user credentials to {self.path}")

    def clear_user_profile(self) -> None:
        """Deletes the user credentials file."""
        if self.path.exists():
            self.path.unlink()
            logger.info("Cleared user credentials.")

    def _load_auth(self) -> AuthModel:
        if not self.path.exists():
            self._auth = AuthModel()
            self._save_auth(self._auth)
            return self._auth

        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            self._auth = AuthModel.model_validate(data)
            return self._auth

    def _save_auth(self, auth: AuthModel):
        with self._lock:
            with AtomicWriter(self.path) as f:
                json.dump(auth.model_dump(), f, indent=2)
            logger.info(f"Successfully saved user credentials to {self.path}")
