from typing import Dict, Any, Optional, TypeVar

PT = TypeVar("PT")

class ClientPayload:
    """|class|

    The base class for the payload which is sent to the endpoint
    when the call is made. This can be subclassed and custom payload
    can be used. If you do not Typehint the function with the custom
    payload then it will automatically use this base payload,
    but keys and values can be accessed like a dictionary or using `X.y`.

    Parameters:
    ----------
    payload: :class:`Dict`
        The payload to be converted.

    Attributes
    ----------
    lenght: `int`
        The lenght of the payload.
    endpoint: `str`
        The endpoint which was called.
    data: `Dict`
        The kwargs from the payload.
    """

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.lenght: int = len(payload)
        self.endpoint: Optional[str] = payload.get("endpoint")
        self.data: Optional[Dict[str, Any]] = payload.get("data")

    def __getitem__(self, __k: str):
        return self.data[__k]

    def __contains__(self, __o: object) -> bool:
        return __o in self.data or __o in self.data.values()

    def __getattribute__(self, __name: str) -> Any:
        try:
            return object.__getattribute__(self, __name)
        except AttributeError:
            return self.data[__name]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} lenght={self.lenght} endpoint={self.endpoint!r}>"

    @property
    def raw(self) -> Dict:
        return self.payload

    @property
    def bot(self) -> Optional[int]:
        """Returns the bot which the endpoint was used."""
        return self.payload.get("__bot__")

    def items(self):
        """|method|

        Returns the payload in the form of dictionary items.
        """
        return self.payload.items()
