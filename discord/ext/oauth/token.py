from dataclasses import dataclass
from datetime import datetime

from ...utils import utcnow


@dataclass
class Token:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: datetime
    scope: str

    def __str__(self) -> str:
        return f"{self.access_token}"

    @property
    def expired(self) -> bool:
        return self.expires_in >= utcnow()
