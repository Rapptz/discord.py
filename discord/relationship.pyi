from .enums import RelationshipType
from .user import User

class Relationship:
    user: User
    type: RelationshipType

    async def delete(self) -> None: ...
    async def accept(self) -> None: ...
