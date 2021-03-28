# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present Trainjo

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

import re

from . import utils
from .enums import ApplicationCommandOptionType, try_enum
from .mixins import Hashable
from .errors import InvalidArgument

__all__ = (
    'ApplicationCommand',
    'ApplicationCommandOption',
    'ApplicationCommandOptionChoice',
)

NAME_PATTERN = re.compile("^[\w-]{1,32}$")
DESCRIPTION_PATTERN = re.compile("^.{1,100}$")
CHOICE_NAME_PATTERN = re.compile("^.{1,100}$")
CHOICE_VALUE_PATTERN = re.compile("^.{1,100}$")

SUB_COMMAND_OPTIONS = (ApplicationCommandOptionType.string,
                       ApplicationCommandOptionType.integer,
                       ApplicationCommandOptionType.boolean,
                       ApplicationCommandOptionType.user,
                       ApplicationCommandOptionType.channel,
                       ApplicationCommandOptionType.role,
                       )
SUB_COMMAND_GROUP_OPTIONS = (ApplicationCommandOptionType.sub_command,
                             )

def is_valid_name(name):
    """Return whether ``name`` is valid as a name for
    :class:`ApplicationCommand` or :class:`ApplicationCommandOption`

    """
    return NAME_PATTERN.match(name) is not None

def is_valid_description(description):
    """Return whether ``description`` is valid as a description for
    :class:`ApplicationCommand` or :class:`ApplicationCommandOption`

    """
    return DESCRIPTION_PATTERN.match(description) is not None

def is_valid_choice_name(name):
    """Return whether ``name`` is valid as a name for
    :class:`ApplicationCommandOptionChoice`

    """
    return CHOICE_NAME_PATTERN.match(name) is not None

def is_valid_choice_value(value):
    """Return whether ``value`` is valid as a value for
    :class:`ApplicationCommandOptionChoice`

    """
    return CHOICE_VALUE_PATTERN.match(value) is not None

class ApplicationCommand(Hashable):
    """Represents a Discord application command.

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)
    
            Return the command's hash

    Attributes
    ----------
    id: :class:`int`
        The command ID.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    guild: Optional[:class:`Guild`]
        The Guild this command belongs to, if any.
    name: :class:`str`
        The name of this command
    description: :class:`str`
        The description of this command.
    options: List[:class:`ApplicationCommandOption`]
        A list of command options.
    
    """

    __slots__ = ('id', 'application_id', 'name', 'description',
                 'options', '_state', 'guild')
    
    def __init__(self, *, state, guild=None, data):
        self._state = state
        self._update(guild=guild, data=data)

    def _update(self, *, guild=None, data):
        self.guild = guild or getattr(self, "guild", None)
        self.id = utils._get_as_snowflake(data, 'id')
        self.application_id = utils._get_as_snowflake(data, 'application_id')
        self.name = data['name']
        self.description = data['description']
        self.options = [ApplicationCommandOption(data=option) for option in data.get('options', [])]

    def __repr__(self):
        result = f"<ApplicationCommand name={self.name} id={self.id} application_id={self.application_id}"
        if self.guild is not None:
            result += f" guild_id={self.guild.id}"
        result += ">"
        return result

    def copy(self):
        """Make a copy of this ApplicationCommmand."""
        data = {'id' : self.id,
                'application_id' : self.application_id,
                'name' : self.name,
                'description' : self.description,
                'options' : [option.to_dict() for option in self.options]}
        return ApplicationCommand(state=self._state, guild=self.guild, data=data)

    async def edit(self, **data):
        """|coro|

        Edit this command.

        Parameters
        -----------
        name: :class:`str`
            The new name for the command.
        description: :class:`str`
            The new description of the command.
        options: Optional[List[:class:`ApplicationCommandOption`]]
            The new list of :class:`ApplicationCommandOption` for this command.
            Can be set to `None` to remove all options from this command.

        Raises
        -------
        :exc:`HTTPException`
            Editing the command failed.

        """

        payload = {}

        name = data.get('name')
        if name is not None:
            payload['name'] = name

        description = data.get('description')
        if description is not None:
            payload['description'] = description

        try:
            options = data['options']
        except KeyError:
            pass
        else:
            if options is not None:
                options = [option.to_dict() for option in options]
            payload['options'] = options

        if self.guild is None:
            data = await self._state.http.edit_global_application_command(self.application_id, self.id, **payload)
        else:
            data = await self._state.http.edit_guild_application_command(self.application_id, self.guild.id,
                                                                         self.id, **payload)
        self._update(data=data)

    async def delete(self):
        """|coro|

        Delete this command.

        Raises
        -------
        :exc:`HTTPException`
            Deleting this command failed.

        """
        if self.guild is None:
            await self._state.http.delete_global_application_command(self.application_id, self.id)
        else:
            await self._state.http.delete_guild_application_command(self.application_id, self.guild.id, self.id)
        self._state._remove_command(self)

class ApplicationCommandOption:
    """Represents an option of a Discord command.

    .. container:: operations

        .. describe:: x == y

            Checks if two options are equal.

        .. describe:: x != y

            Checks if two options are not equal.

    Attributes
    -----------
    name: :class:`str`
        The name of the command option.
    description: :class:`str`
        The description of the command option.
    required: :class:`bool`
        Whether this command option is required or optional.
    choices: List[:class:`ApplicationCommandOptionChoice`]
        A list of choices for this command option. Only non-empty when the command option
        has type :attr:`.enums.ApplicationCommandOptionType.string`
        or :attr:`.enums.ApplicationCommandOptionType.integer`.
    options: List[:class:`ApplicationCommandOption`]
        A list of options for this command option. Only non-empty when the command option
        has type :attr:`.enums.ApplicationCommandOptionType.sub_command`
        or :attr:`.enums.ApplicationCommandOptionType.sub_command_group`.

    """

    __slots__ = ('_state', '_type', 'name', 'description', 'required',
                 'choices', 'options')

    def __init__(self, *, data):
        self._update(data)

    def _update(self, data):
        self._type = data['type']
        self.name = data['name']
        self.description = data['description']
        self.required = data.get('required', False)
        self.choices = [ApplicationCommandOptionChoice(data=choice) for choice in data.get('choices', [])]
        self.options = [ApplicationCommandOption(data=option) for option in data.get('options', [])]

    @property
    def type(self):
        """:class:`.enums.ApplicationCommandOptionType`: The type of the command option."""
        return try_enum(ApplicationCommandOptionType, self._type)

    def to_dict(self):
        result = {'type' : self.type.value,
                  'name' : self.name,
                  'description' : self.description}
        if self.required:
            result['required'] = self.required
        if len(self.choices) > 0:
            result['choices'] = [choice.to_dict() for choice in self.choices]
        if len(self.options) > 0:
            result['options'] = [option.to_dict() for option in self.options]
        return result

    def __eq__(self, other):
        return (isinstance(other, ApplicationCommandOption) and
                self.type == other.type and
                self.name == other.name and
                self.required == other.required and
                self.choices == other.choices and
                self.options == other.options)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"<ApplicationCommandOption type={self.type} name={self.name}>"

    @classmethod
    def SubCommand(cls, *, name, description, options=None):
        """Create a command option that is a sub command.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the command. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the command.
        options: Optional[List[:class:`.ApplicationCommandOption`]]
            A list of options for the command. Can be set to ``None`` to not include any options.
            May not contain options of type :attr:`.enums.ApplicationCommandOptionType.sub_command`
            or :attr:`.enums.ApplicationCommandOptionType.sub_command_group`. Can contain at most
            25 options.

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        if options is None:
            options = []
        if len(options) > 25:
            raise InvalidArgument(f"The options '{options}' contain more than 25 choices.")
        for option in options:
            if option.type not in SUB_COMMAND_OPTIONS:
                raise InvalidArgument(f"Options of type '{option.type}' are invalid for sub commands.")
        t = ApplicationCommandOptionType.sub_command
        return cls(data={'type' : t, 'name' : name, 'description' : description,
                         'options' : [option.to_dict() for option in options]})

    @classmethod
    def SubCommandGroup(cls, *, name, description, options=None):
        """Create a command option that is a sub command group.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the command group. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the command group.
        options: Optional[List[:class:`.ApplicationCommandOption`]]
            A list of options for the command group. Can be set to ``None`` to not include any options.
            May only contain options of type :attr:`.enums.ApplicationCommandOptionType.sub_command`.
            Can contain at most 25 options.

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        if options is None:
            options = []
        if len(options) > 25:
            raise InvalidArgument(f"The options '{options}' contain more than 25 choices.")
        for option in options:
            if option.type not in SUB_COMMAND_GROUP_OPTIONS:
                raise InvalidArgument(f"Options of type '{option.type}' are invalid for sub command groups.")
        t = ApplicationCommandOptionType.sub_command_group
        return cls(data={'type' : t, 'name' : name, 'description' : description,
                         'options' : [option.to_dict() for option in options]})

    @classmethod
    def String(cls, *, name, description, required=True, choices=None):
        """Create a command option that is a String argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```
        choices: Optional[Mapping[:class:`str`, :class`str`]]
            A mapping of choice names to their corresponding values. If set to ``None`` this option
            will have no choices, but accepts any :class:`str`. There may be at most 25 choices,
            where each choice name and value must be between 1 and 100 characters.

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        if choices is None:
            choices = {}
        if len(choices) > 25:
            raise InvalidArgument(f"The choices '{choices}' contain more than 25 choices.")
        choice_list = []
        for n, v in choices.items():
            if not is_valid_choice_name(n):
                raise InvalidArgument(f"The name '{n}' is not valid for a choice.")
            if not is_valid_choice_value(v):
                raise InvalidArgument(f"The value '{v}' is not valid for a choice.")
            choice_list.append({'name' : n, 'value' : v})
        t = ApplicationCommandOptionType.string
        return cls(data={'type' : t, 'name' : name, 'description' : description,
                         'required' : required, 'choices' : choice_list})

    @classmethod
    def Integer(cls, *, name, description, required=True, choices=None):
        """Create a command option that is a Integer argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```
        choices: Optional[Mapping[:class:`str`, :class`int`]]
            A mapping of choice names to their corresponding values. If set to ``None`` this option
            will have no choices, but accepts any :class:`int`. There may be at most 25 choices,
            where each choice name must be between 1 and 100 characters.

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        if choices is None:
            choices = {}
        if len(choices) > 25:
            raise InvalidArgument(f"The choices '{choices}' contain more than 25 choices.")
        choice_list = []
        for n, v in choices.items():
            if not is_valid_choice_name(n):
                raise InvalidArgument(f"The name '{n}' is not valid for a choice.")
            if not isinstance(v, int):
                raise InvalidArgument(f"The value '{v}' is not valid for a choice.")
            choice_list.append({'name' : n, 'value' : v})
        t = ApplicationCommandOptionType.integer
        return cls(data={'type' : t, 'name' : name, 'description' : description,
                         'required' : required, 'choices' : choice_list})

    @classmethod
    def Boolean(cls, *, name, description, required=True):
        """Create a command option that is a Boolean argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        t = ApplicationCommandOptionType.boolean
        return cls(data={'type' : t, 'name' : name, 'description' : description, 'required' : required})

    @classmethod
    def User(cls, *, name, description, required=True):
        """Create a command option that is a User argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        t = ApplicationCommandOptionType.user
        return cls(data={'type' : t, 'name' : name, 'description' : description, 'required' : required})

    @classmethod
    def Channel(cls, *, name, description, required=True):
        """Create a command option that is a Channel argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        t = ApplicationCommandOptionType.channel
        return cls(data={'type' : t, 'name' : name, 'description' : description, 'required' : required})

    @classmethod
    def Role(cls, *, name, description, required=True):
        """Create a command option that is a Role argument.

        Attributes
        -----------
        name: :class:`str`
            The 1-32 character name of the argument. It may only consist of letters
            and the dash '-' symbol.
        description: :class:`str`
            The 1-100 character description of the argument.
        required: :class:`bool`
            Whether this argument is required or optional. By default set to ``True```

        Raises
        -------
        :exc:`.InvalidArgument`
            One of the arguments is invalid.
        
        """
        if not is_valid_name(name):
            raise InvalidArgument(f"The name '{name}' is not valid.")        
        if not is_valid_description(description):
            raise InvalidArgument(f"The description '{description}' is not valid.")
        t = ApplicationCommandOptionType.role
        return cls(data={'type' : t, 'name' : name, 'description' : description, 'required' : required})

class ApplicationCommandOptionChoice:
    """Represents a choice for a Discord command option.

    .. container:: operations

        .. describe:: x == y

            Checks if two options are equal.

        .. describe:: x != y

            Checks if two options are not equal.

    Attributes
    -----------
    name: :class:`str`
        The name of the choice.
    value: Union[:class:`str`, :class:`int`]
        The value of the choice. The type of the value depends on
        the type of the corresponding option.

    """

    def __init__(self, *, data):
        self._update(data)

    def _update(self, data):
        self.name = data['name']
        self.value = data['value']

    def to_dict(self):
        return {'name' : self.name,
                'value' : self.value}

    def __eq__(self, other):
        return (isinstance(other, ApplicationCommandOptionChoice) and
                self.name == other.name and
                self.value == other.value)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"<ApplicationCommandOptionChoice name={self.name} value={self.value}>"

