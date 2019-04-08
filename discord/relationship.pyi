from .enums import RelationshipType
from .user import User

class Relationship:
    user: User
    type: RelationshipType

    def __repr__(self) -> str: ...
    async def delete(self) -> None: ...
    async def accept(self) -> None: ...
