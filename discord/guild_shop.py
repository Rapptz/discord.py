"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Optional,
    Dict,
    Union,
    Any,
    Tuple
)

from . import utils
from .enums import (
    CountryCode,
    GuildShopSortType,
    try_enum
)

if TYPE_CHECKING:
    from .types.guild import (
        GuildShopProduct as GuildShopProductPayload,
        GuildShop as GuildShopPayload,
        GuildProductTrial as GuildProductTrialPayload,
        ActiveTrial as ActiveTrialPayload
    )
    from .role import Role
    from .state import ConnectionState

__all__ = (
    "ActiveProductTrial",
    "GuildShopProduct",
    "GuildProductTrial",
    "GuildShop"
)

MISSING = utils.MISSING

class ActiveProductTrial:
    """Represents an active product trial.

    .. container:: operations

        .. describe:: int(x)

            Returns the product ID.

    Attributes
    ----------
    id: :class:`int`
        The product ID this active trial belongs to.
    interval: :class:`int`
        ...
    interval_count: :class:`int`
        ...
    sku_id: :class:`int`
        The SKU ID the product belongs to.
    """

    __slots__ = (
        "id",
        "interval",
        "interval_count",
        "sku_id",

        "_state"
    )

    def __init__(self, *, data: ActiveTrialPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state

        self.id: int = int(data.get("id"))
        """The product ID this active trial belongs to"""
        self.interval: int = int(data.get("interval"))
        """..."""
        self.interval_count: int = int(data.get("interval_count"))
        """..."""
        self.sku_id: int = int(data.get("sku_id"))
        """The SKU ID the product belongs to"""

    def __int__(self) -> int:
        return self.id
    
    def __repr__(self) -> str:
        return (
            f"<ActiveTrial id={self.id} sku_id={self.sku_id}>"
        )

class GuildProductTrial:
    """Represents a trial of a product in the guild shop.

    .. container:: operations

        .. describe:: int(x)

            Returns the product ID.
    
    Attributes
    ----------
    id: :class:`int`
        The ID of the product.
    active_trials: :class:`int`
        The number of users with this trial active.
    max_active_trials: :class:`int`
        The maximum number of trials available in guild level. If None, it has no limit.
    active: Optional[:class:`ActiveProductTrial`]
        The active product trials.
    """

    def __init__(self, *, data: GuildProductTrialPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state

        self.id: int = int(data.get("id"))
        """The ID of the product"""
        self.active_trials: int = int(data.get("num_active_trial_users"))
        """The number of users with this trial active"""
        self.max_active_trials: Optional[int] = data.get("max_num_active_trial_users", None)
        """The maxmimum number of trials available in guild level. If None, it has no limit"""
        self.active: Optional[ActiveProductTrial] = ActiveProductTrial(data=data.get("active_trial"), state=state) if data.get("active_trial") else None
        """The active product trials"""

    def __int__(self) -> int:
        return self.id
    
    def __repr__(self) -> str:
        return (
            f"<ProductTrial id={self.id}>"
        )

class GuildShopProduct:
    """Represents a guild shop product.
    
    .. container:: operations

        .. describe:: str(x)

            Returns the product's name

    Attributes
    ----------
    id: :class:`int`
        The product ID.
    application_id: :class:`int`
        ...
    guild_id: :class:`int`
        The guild ID this product is in.
    name: :class:`str`
        The product name.
    price_tier: :class:`float`
        The product buying price. This is, by default, in US$.
    description: Optional[:class:`str`]
        The long description of the product.
    role_id: Optional[:class:`int`]
        The ID for the role that is given when buying this product.

    .. versionadded:: 2.4
    """

    __slots__ = (
        "id",
        "application_id",
        "guild_id",
        "name",
        "price_tier",
        "description",
        "role_id",

        "_state"
    )

    def __init__(self, *, data: GuildShopProductPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state

        self.id: int = int(data.get("id"))
        """The product ID"""
        self.application_id: int = int(data.get("application_id"))
        """..."""
        self.guild_id: int = int(data.get("guild_id"))
        """The guild the product is in"""
        self.name: str = data.get("name")
        """The product name"""
        self.price_tier: float = data.get("price_tier")
        """The product buying price. This is, by default, in US$"""
        self.description: Optional[str] = data.get("description", None)
        """The long description of the product"""
        self.role_id: Optional[int] = data.get("role_id", None)
        """The ID for the role that is given when buying this product"""

    def __repr__(self) -> str:
        return (
            "<GuildShopProduct "
            f"id={self.id} application_id={self.application_id} "
            f"guild_id={self.guild_id} name={self.name!r}>"
        )
    
    def __str__(self) -> str:
        return self.name

    async def edit(
        self,
        *,
        name: str = MISSING,
        price_tier: float = MISSING,
        description: str = MISSING,
        role: Role = MISSING,
    ) -> None:
        """|coro|

        Edits this guild product.

        You must have :attr:`~Permissions.manage_guild` to do this

        Parameters
        ----------
        name: :class:`str`
            The product name. Cannot be None.
        price_tier: :class:`float`
            The product price. Cannot be None.
        description: :class:`str`
            The product description.
        role_id: :class:`Role`
            The role given when a user buys the product.
        
        Raises
        ------
        Forbidden
            You are not allowed to edit guild products.
        HTTPException
            An error occurred while deleting the product.
        """

        payload: Dict[str, Union[str, float, int]] = {}

        payload['description'] = description
        payload['role_id'] = role.id

        if name is not MISSING:
            if name is None:
                raise ValueError("'name' can't be None when editing a guild product")
            
            payload['name'] = name

        if price_tier is not MISSING:
            if price_tier is None or price_tier < 0:
                raise ValueError("'price_tier' can't be None or less than 0")
            
            payload['price_tier'] = price_tier

        await self._state.http.edit_guild_product(self.guild_id, self.id, payload=payload)

    async def delete(self, *, reason: str = MISSING) -> None:
        """|coro|
        
        Deletes the current product from the guild's shop.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Parameters
        ----------
        reason: :class:`str`
            The reason for deleting this product. Shows up in the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to delete guild products.
        HTTPException
            An error occurred while deleting the product.
        """

        await self._state.http.delete_guild_shop_product(self.guild_id, self.id, reason=reason)

class GuildShop:
    """Represents a guild Shop.

    .. container::

        .. describe:: x == y

            Checks if two shops are equal.

        .. describe:: x != y

            Checks if two shops are not equal.

    Attributes
    ----------
    guild_id: :class:`int`
        The guild ID this shop is linked to.
    full_server_gate: :class:`bool`
        ...
    description: Optional[:class:`str`]
        The guild's shop description.
    primary_color: Optional[:class:`Any`]
        The guild's shop primary color.
    primary_colour: Optional[:class:`Any`]
        The guild's shop primary colour.
    trailer_url: Optional[:class:`str`]
        The URL of the trailer shown when users go to the shop page.
    show_subscriber_count: :class:`bool`
        If the member count that bought a server subscription is shown to everyone.
    products_sort_type: Optional[:class:`GuildShopSortType`]
        The sort order the products will follow.
    image_asset: Optional[:class:`Asset`]
        The image asset shown when accessing the shop.
    slug: Optional[:class:`str`]
        A system-generated URL referring to the shop

    .. versionadded:: 2.4
    """

    __slots__ = (
        "guild_id",
        "full_server_gate",
        "description",
        "trailer_url",
        "primary_color",
        "products_sort_type",
        "show_subscriber_count",
        "slug",

        "_state",
    )

    def __init__(self, *, data: GuildShopPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state

        self.guild_id: int = int(data.get("guild_id")) # MyPy syntax highlighting
        """The guild ID this shop is linked to"""
        self.full_server_gate: bool = data.get("full_server_gate", False)
        """..."""
        self.description: Optional[str] = data.get("description", None)
        """The guild's shop description"""
        self.trailer_url: Optional[str] = data.get("store_page_trailer_url", None)
        """The URL of the trailer shown when users go to the shop page"""
        self.primary_color: Optional[Any] = data.get("store_page_primary_color", None)
        """The guild's shop primary color"""
        self.products_sort_type: Optional[GuildShopSortType] = try_enum(GuildShopSortType, data.get("store_page_guild_products_default_sort", 1))
        """The sort order the products will follow"""
        self.show_subscriber_count: bool = data.get("store_page_show_subscriber_count", False)
        """If the member count that bought a server subscription is shown to everyone"""
        self.slug: Optional[str] = data.get("store_page_slug", None)
        """A system-generated URL referring to the shop"""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GuildShop) or not isinstance(self, GuildShop):
            return NotImplemented

        return other.guild_id == self.guild_id

    @property
    def primary_colour(self) -> Any:
        """The guild's shop primary colour"""
        return self.primary_color
    
    async def edit(
        self,
        *,
        description: Optional[str] = MISSING,
        primary_color: Any = MISSING,
        primary_colour: Any = MISSING,
        trailer_url: str = MISSING,
        show_subscriber_count: bool = MISSING
    ) -> None:
        """|coro|
        
        Edits the Guild Shop.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Parameters
        ----------
        description: Optional[:class:`str`]
            The shop description. If ``None``, it resets it.
        primary_color: :class:`Any`
            The shop primary color.
        primary_colour: :class:`Any`
            An alias for :param:``primary_color``.
        trailer_url: :class:`str`
            The trailer URL that is shown to users when accessing the shop.
        show_subscriber_count: :class:`bool`
            Whether to show the member count that bought in this shop.
        """

        payload = {}

        if description is not MISSING:
            payload['description'] = description

        if primary_color is not MISSING and primary_colour is not MISSING:
            raise ValueError("You passed both 'primary_color' and 'primary_colour' parameters. Pass one, not both.")
        
        if primary_color is not MISSING:
            payload['store_page_primary_color'] = primary_color

        elif primary_colour is not MISSING:
            payload['store_page_primary_color'] = primary_colour

        if trailer_url is not MISSING:
            payload['store_page_trailer_url'] = trailer_url

        if show_subscriber_count is not MISSING:
            payload['store_page_show_subscriber_count'] = show_subscriber_count

        await self._state.http.edit_guild_shop(self.guild_id, payload=payload)
    
    async def create_product(
        self,
        *,
        name: str,
        price_tier: float,
        description: str = MISSING,
        role: Role = MISSING
    ) -> GuildShopProduct:
        """|coro|
        
        Creates a :class:`GuildShopProduct`.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Parameters
        ----------
        name: :class:`str`
            The product name.
        price_tier: :class:`float`
            The product price.
        description: :class:`str`
            The description for the product. Can be None
        role: :class:`Role`
            The role that is going to be given when buying the product.
        
        Raises
        ------
        Forbidden
            You are not allowed to create products.
        HTTPException
            An error occurred while creating the product.

        Returns
        -------
        The created Guild Shop Product
        """

        payload: Dict[str, Union[str, float, list, tuple, None]] = {
            "name": name,
            "price_tier": price_tier,
            "description": description or None,
            "role_id": role.id or None
        }

        data = await self._state.http.create_guild_shop_product(self.guild_id, payload=payload)
        product = GuildShopProduct(data=data, state=self._state)

        return product
    
    async def products(self, *, country: CountryCode = MISSING) -> Tuple[GuildShopProduct, ...]:
        """|coro|
        
        Fetches and returns a tuple containing all :class:`GuildShopProduct`
        available in the guild.

        Parameters
        ----------
        country_code: Union[:class:`str`, :class:`Locale`]
            The country code.
            This country code will add a field into the GuildShopProduct that
            is the US$ price "translated" to that country's currency.

        Raises
        ------
        HTTPException
            An error occurred while fetching the guild products.

        Returns
        -------
        A tuple containing all Guild Shop Products
        """

        if country is not MISSING:
            if not isinstance(country, CountryCode):
                raise ValueError(f"Expected CountryCode in 'country', got '{country.__class__.__name__}' instead")
            
            code: str = country.value

        else:
            code: str = CountryCode.united_states_of_america.value # Using this in case something changes (NOT POSSIBLY AT ALL) this will remain the same.

        data = await self._state.http.get_guild_shop_products(self.guild_id, country_code=code)

        return tuple(GuildShopProduct(data=d, state=self._state) for d in data['listings'])
    
    async def fetch_product_trials(self) -> Tuple[GuildProductTrial, ...]:
        """|coro|
        
        Fetches and returns a tuple containing all :class:`GuildProductTrial`
        for the products in the shop.

        Raises
        ------
        HTTPException
            An error occurred while fetching the trials.

        Returns
        -------
        A tuple containing all Guild Shop Product Trials.
        """

        data = await self._state.http.get_guild_subcriptions_trials(self.guild_id)

        return tuple(GuildProductTrial(data=d, state=self._state) for d in data)
