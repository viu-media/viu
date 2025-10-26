from httpx import Client
from ....core.utils.networking import random_user_agent


class MangaProvider:
    session: Client

    USER_AGENT = random_user_agent()
    HEADERS = {}

    def __init__(self) -> None:
        self.session = Client(
            headers={
                "User-Agent": self.USER_AGENT,
                **self.HEADERS,
            },
            timeout=10,
        )
