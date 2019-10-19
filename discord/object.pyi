from .mixins import Hashable
import datetime

class Object(Hashable):
    id: int

    def __init__(self, id: int) -> None: ...
    @property
    def created_at(self) -> datetime.datetime: ...
