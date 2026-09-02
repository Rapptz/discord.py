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

import datetime
from typing import TYPE_CHECKING, List, Optional, Sequence, Union

from . import utils
from .enums import JoinRequestStatus, MemberVerificationFieldType, try_enum
from .mixins import Hashable
from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .guild import Guild
    from .state import ConnectionState
    from .types.member_verification import (
        JoinRequest as JoinRequestPayload,
        MemberVerification as MemberVerificationPayload,
        MemberVerificationFormField as MemberVerificationFormFieldPayload,
    )
    from .user import User

__all__ = (
    'MemberVerificationFormField',
    'MemberVerification',
    'JoinRequest',
)


class MemberVerificationFormField:
    """Represents a question on a guild's :class:`MemberVerification`.

    .. versionadded:: 2.8

    .. container:: operations

        .. describe:: str(x)

            Returns the form field's label.

    Parameters
    -----------
    type: :class:`MemberVerificationFieldType`
        The type of question being asked.
    label: :class:`str`
        The label of the form field. Can be up to 300 characters long.
    choices: Optional[List[:class:`str`]]
        The multiple choice answers to the question. There can be up to 8 choices,
        each up to 150 characters long.

        Only applicable to :attr:`MemberVerificationFieldType.multiple_choice`.
    values: Optional[List[:class:`str`]]
        The rules the user must agree to. There can be up to 16 rules,
        each up to 300 characters long.

        Only applicable to :attr:`MemberVerificationFieldType.terms`.
    required: :class:`bool`
        Whether the question must be answered for the application to be submitted.
    description: Optional[:class:`str`]
        The subtext of the form field.
    placeholder: Optional[:class:`str`]
        The placeholder text shown in the field's response area.

        Only applicable to :attr:`MemberVerificationFieldType.text_input` and
        :attr:`MemberVerificationFieldType.paragraph`.

    Attributes
    -----------
    type: :class:`MemberVerificationFieldType`
        The type of question being asked.
    label: :class:`str`
        The label of the form field.
    choices: Optional[List[:class:`str`]]
        The multiple choice answers to the question.
    values: Optional[List[:class:`str`]]
        The rules the user must agree to.
    required: :class:`bool`
        Whether the question must be answered for the application to be submitted.
    description: Optional[:class:`str`]
        The subtext of the form field.
    placeholder: Optional[:class:`str`]
        The placeholder text shown in the field's response area.
    response: Optional[Union[:class:`str`, :class:`bool`]]
        The applicant's response to the question, if this field came from a
        :class:`JoinRequest`.

        For :attr:`MemberVerificationFieldType.terms` this is ``True``, and for
        :attr:`MemberVerificationFieldType.multiple_choice` this is the text of
        the selected :attr:`choices` entry.
    """

    __slots__ = (
        'type',
        'label',
        'choices',
        'values',
        'required',
        'description',
        'placeholder',
        'response',
    )

    def __init__(
        self,
        *,
        type: MemberVerificationFieldType,
        label: str,
        choices: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
        required: bool = True,
        description: Optional[str] = None,
        placeholder: Optional[str] = None,
    ) -> None:
        self.type: MemberVerificationFieldType = type
        self.label: str = label
        self.choices: Optional[List[str]] = choices
        self.values: Optional[List[str]] = values
        self.required: bool = required
        self.description: Optional[str] = description
        self.placeholder: Optional[str] = placeholder
        self.response: Optional[Union[str, bool]] = None

    def __repr__(self) -> str:
        return f'<MemberVerificationFormField type={self.type!r} label={self.label!r} required={self.required}>'

    def __str__(self) -> str:
        return self.label

    @classmethod
    def _from_data(cls, data: MemberVerificationFormFieldPayload) -> Self:
        self = cls(
            type=try_enum(MemberVerificationFieldType, data['field_type']),
            label=data['label'],
            choices=data.get('choices'),
            values=data.get('values'),
            required=data['required'],
            description=data.get('description'),
            placeholder=data.get('placeholder'),
        )

        response = data.get('response')
        if self.type is MemberVerificationFieldType.multiple_choice and isinstance(response, int):
            # Multiple choice responses are sent as an index into the choices
            choices = self.choices or []
            if 0 <= response < len(choices):
                response = choices[response]
        self.response = response  # type: ignore
        return self

    def to_dict(self) -> MemberVerificationFormFieldPayload:
        payload: MemberVerificationFormFieldPayload = {
            'field_type': self.type.value,
            'label': self.label,
            'required': self.required,
            'description': self.description,
        }
        if self.choices is not None:
            payload['choices'] = self.choices
        if self.values is not None:
            payload['values'] = self.values
        if self.placeholder is not None:
            payload['placeholder'] = self.placeholder

        return payload


class MemberVerification:
    """Represents a guild's member verification gate.

    This is the set of questions a user must answer before they are able to
    participate in a guild.

    .. versionadded:: 2.8

    .. container:: operations

        .. describe:: len(x)

            Returns the number of form fields.

        .. describe:: iter(x)

            Returns an iterator over the form fields.

    Attributes
    -----------
    guild: :class:`Guild`
        The guild this member verification is for.
    version: :class:`datetime.datetime`
        When the member verification was last modified.
    form_fields: List[:class:`MemberVerificationFormField`]
        The questions the user must answer.
    description: Optional[:class:`str`]
        A description of what the guild is about. This can be different than
        the guild's own description.
    """

    __slots__ = ('_state', 'guild', 'version', 'form_fields', 'description')

    def __init__(self, *, data: MemberVerificationPayload, guild: Guild) -> None:
        self._state: ConnectionState = guild._state
        self.guild: Guild = guild
        self._update(data)

    def _update(self, data: MemberVerificationPayload) -> None:
        self.version: datetime.datetime = utils.parse_time(data['version'])
        self.form_fields: List[MemberVerificationFormField] = [
            MemberVerificationFormField._from_data(field) for field in data.get('form_fields', [])
        ]
        self.description: Optional[str] = data.get('description')

    def __repr__(self) -> str:
        return f'<MemberVerification guild={self.guild!r} form_fields={len(self.form_fields)}>'

    def __len__(self) -> int:
        return len(self.form_fields)

    def __iter__(self):
        return iter(self.form_fields)

    @property
    def enabled(self) -> bool:
        """:class:`bool`: Whether the member verification gate is enabled."""
        return 'MEMBER_VERIFICATION_GATE_ENABLED' in self.guild.features

    @property
    def manual_approval(self) -> bool:
        """:class:`bool`: Whether join requests for this guild must be manually approved.

        This is the case when any question is of a type other than
        :attr:`MemberVerificationFieldType.terms`.
        """
        return any(field.type is not MemberVerificationFieldType.terms for field in self.form_fields)

    async def edit(
        self,
        *,
        enabled: bool = MISSING,
        form_fields: Sequence[MemberVerificationFormField] = MISSING,
        description: Optional[str] = MISSING,
        bulk_action: JoinRequestStatus = MISSING,
        reason: Optional[str] = None,
    ) -> MemberVerification:
        """|coro|

        Edits the member verification gate.

        You must have :attr:`~Permissions.manage_guild` to do this.

        All parameters are optional.

        Parameters
        -----------
        enabled: :class:`bool`
            Whether the member verification gate is enabled.
        form_fields: List[:class:`MemberVerificationFormField`]
            The questions the user must answer. There can be up to 5 questions.

            Using a field type other than :attr:`MemberVerificationFieldType.terms`
            requires the guild to have the ``MEMBER_VERIFICATION_MANUAL_APPROVAL`` feature.
        description: Optional[:class:`str`]
            A description of what the guild is about. Can be up to 300 characters long.
        bulk_action: :class:`JoinRequestStatus`
            What to do with the pending join requests when disabling the gate.
            Only :attr:`JoinRequestStatus.approved` and :attr:`JoinRequestStatus.rejected`
            can be used. Defaults to approving.
        reason: Optional[:class:`str`]
            The reason for editing the member verification. Shows up on the audit log.

        Raises
        -------
        ValueError
            An invalid ``bulk_action`` was passed.
        Forbidden
            You do not have permissions to edit the member verification.
        HTTPException
            Editing the member verification failed.

        Returns
        --------
        :class:`MemberVerification`
            The newly updated member verification.
        """
        return await self.guild.edit_member_verification(
            enabled=enabled,
            form_fields=form_fields,
            description=description,
            bulk_action=bulk_action,
            reason=reason,
        )


class JoinRequest(Hashable):
    """Represents a request to join a guild with member verification enabled.

    .. versionadded:: 2.8

    .. container:: operations

        .. describe:: x == y

            Checks if two join requests are equal.

        .. describe:: x != y

            Checks if two join requests are not equal.

        .. describe:: hash(x)

            Returns the join request's hash.

    Attributes
    -----------
    id: :class:`int`
        The join request's ID.
    guild_id: :class:`int`
        The ID of the guild this join request is for.
    user_id: :class:`int`
        The ID of the user who created this join request.
    user: Optional[:class:`User`]
        The user who created this join request, if available.
    status: :class:`JoinRequestStatus`
        The status of the join request.
    created_at: :class:`datetime.datetime`
        When the join request was created.
    form_responses: Optional[List[:class:`MemberVerificationFormField`]]
        The user's responses to the guild's member verification questions,
        if available.
    last_seen: Optional[:class:`datetime.datetime`]
        When the join request was acknowledged by the user, if it has been.
    actioned_at: Optional[:class:`datetime.datetime`]
        When the join request was actioned, if it has been.
    actioned_by: Optional[:class:`User`]
        The moderator who actioned the join request, if available.
    rejection_reason: Optional[:class:`str`]
        Why the join request was rejected, if it was.
    interview_channel_id: Optional[:class:`int`]
        The ID of the group channel where an interview regarding this join request
        may be conducted, if any.
    """

    __slots__ = (
        '_state',
        'id',
        'guild_id',
        'user_id',
        'user',
        'status',
        'created_at',
        'form_responses',
        'last_seen',
        'actioned_at',
        'actioned_by',
        'rejection_reason',
        'interview_channel_id',
    )

    def __init__(self, *, data: JoinRequestPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: JoinRequestPayload) -> None:
        state = self._state

        self.id: int = int(data['id'])
        self.guild_id: int = int(data['guild_id'])
        self.user_id: int = int(data['user_id'])
        self.status: JoinRequestStatus = try_enum(JoinRequestStatus, data['application_status'])
        self.created_at: datetime.datetime = utils.parse_time(data['created_at'])
        self.last_seen: Optional[datetime.datetime] = utils.parse_time(data.get('last_seen'))
        self.rejection_reason: Optional[str] = data.get('rejection_reason')
        self.interview_channel_id: Optional[int] = utils._get_as_snowflake(data, 'interview_channel_id')

        self.actioned_at: Optional[datetime.datetime] = utils.parse_time(data.get('reviewed_at'))

        form_responses = data.get('form_responses')
        self.form_responses: Optional[List[MemberVerificationFormField]] = (
            [MemberVerificationFormField._from_data(field) for field in form_responses]
            if form_responses is not None
            else None
        )

        user = data.get('user')
        self.user: Optional[User] = state.store_user(user) if user is not None else state.get_user(self.user_id)

        actioned_by = data.get('actioned_by_user')
        self.actioned_by: Optional[User] = state.store_user(actioned_by) if actioned_by is not None else None

    def __repr__(self) -> str:
        return f'<JoinRequest id={self.id} user_id={self.user_id} status={self.status!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this join request is for, if cached."""
        return self._state._get_guild(self.guild_id)

    def is_acked(self) -> bool:
        """:class:`bool`: Whether the join request has been acknowledged by the user."""
        return self.last_seen is not None

    async def approve(self) -> JoinRequest:
        """|coro|

        Approves the join request.

        You must have :attr:`~Permissions.kick_members` to do this.

        Raises
        -------
        Forbidden
            You do not have permissions to action the join request.
        HTTPException
            Actioning the join request failed.

        Returns
        --------
        :class:`JoinRequest`
            The newly updated join request.
        """
        data = await self._state.http.action_join_request(self.guild_id, self.id, JoinRequestStatus.approved.value)
        self._update(data)
        return self

    async def reject(self, *, reason: Optional[str] = None) -> JoinRequest:
        """|coro|

        Rejects the join request.

        You must have :attr:`~Permissions.kick_members` to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for rejecting the join request. Can be up to 160 characters long.

        Raises
        -------
        Forbidden
            You do not have permissions to action the join request.
        HTTPException
            Actioning the join request failed.

        Returns
        --------
        :class:`JoinRequest`
            The newly updated join request.
        """
        data = await self._state.http.action_join_request(
            self.guild_id, self.id, JoinRequestStatus.rejected.value, rejection_reason=reason
        )
        self._update(data)
        return self
