"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import TYPE_CHECKING, Iterator, List, Optional, Sequence, Tuple, Union

from .enums import ExperimentFilterType, try_enum
from .metadata import Metadata
from .utils import SequenceProxy, SnowflakeList, murmurhash32

if TYPE_CHECKING:
    from .abc import Snowflake
    from .guild import Guild
    from .state import ConnectionState
    from .types.experiment import (
        Filters as FiltersPayload,
        GuildExperiment as GuildExperimentPayload,
        Override as OverridePayload,
        Population as PopulationPayload,
        Rollout as RolloutPayload,
        UserExperiment as AssignmentPayload,
    )

__all__ = (
    'ExperimentRollout',
    'ExperimentFilter',
    'ExperimentPopulation',
    'ExperimentOverride',
    'HoldoutExperiment',
    'GuildExperiment',
    'UserExperiment',
)


class ExperimentRollout:
    """Represents a rollout for an experiment population.

    .. container:: operations

        .. describe:: x in y

            Checks if a position is eligible for the rollout.

    .. versionadded:: 2.1

    Attributes
    -----------
    population: :class:`ExperimentPopulation`
        The population this rollout belongs to.
    bucket: :class:`int`
        The bucket the rollout grants.
    ranges: List[Tuple[:class:`int`, :class:`int`]]
        The position ranges of the rollout.
    """

    __slots__ = ('population', 'bucket', 'ranges')

    def __init__(self, population: ExperimentPopulation, data: RolloutPayload):
        bucket, ranges = data

        self.population = population
        self.bucket: int = bucket
        self.ranges: List[Tuple[int, int]] = [(range['s'], range['e']) for range in ranges]

    def __repr__(self) -> str:
        return f'<ExperimentRollout bucket={self.bucket} ranges={self.ranges!r}>'

    def __contains__(self, item: int, /) -> bool:
        for start, end in self.ranges:
            if start <= item <= end:
                return True
        return False


class ExperimentFilter:
    """Represents a filter for an experiment population.

    This is a purposefuly very low-level object.

    .. container:: operations

        .. describe:: x in y

            Checks if a guild fulfills the filter requirements.

    .. versionadded:: 2.1

    Attributes
    -----------
    population: :class:`ExperimentPopulation`
        The population this filter belongs to.
    type: :class:`ExperimentFilterType`
        The type of filter.
    options: :class:`Metadata`
        The parameters for the filter.
        If known, murmur3-hashed keys are unhashed to their original names.
    """

    __slots__ = ('population', 'type', 'options')

    # Most of these are taken from the client
    FILTER_KEYS = {
        1604612045: 'guild_has_feature',
        2404720969: 'guild_id_range',
        2918402255: 'guild_member_count_range',
        3013771838: 'guild_ids',
        4148745523: 'guild_hub_types',
        188952590: 'guild_has_vanity_url',
        2294888943: 'guild_in_range_by_hash',
        3399957344: 'min_id',
        1238858341: 'max_id',
        2690752156: 'hash_key',
        1982804121: 'target',
        1183251248: 'guild_features',
    }

    def __init__(self, population: ExperimentPopulation, data: FiltersPayload):
        type, options = data

        self.population = population
        self.type: ExperimentFilterType = try_enum(ExperimentFilterType, type)

        self.options = metadata = Metadata()
        for key, value in options:
            try:
                key = self.FILTER_KEYS[int(key)]
            except (KeyError, ValueError):
                pass
            if isinstance(value, str) and value.isdigit():
                value = int(value)

            metadata[str(key)] = value

    def __repr__(self) -> str:
        return f'<ExperimentFilter type={self.type!r} options={self.options!r}>'

    def __contains__(self, guild: Guild, /) -> bool:
        return self.is_eligible(guild)

    @staticmethod
    def in_range(num: int, start: Optional[int], end: Optional[int], /) -> bool:
        if start is not None and num < start:
            return False
        if end is not None and num > end:
            return False
        return True

    def is_eligible(self, guild: Guild, /) -> bool:
        """Checks whether the guild fulfills the filter requirements.

        .. note::

            This function is not intended to be used directly. Instead, use :func:`GuildExperiment.bucket_for`.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to check.

        Returns
        --------
        :class:`bool`
            Whether the guild fulfills the filter requirements.
        """
        type = self.type
        options = self.options

        if type == ExperimentFilterType.feature:
            # One feature must be present
            return options.guild_features and any(feature in guild.features for feature in options.guild_features)
        elif type == ExperimentFilterType.id_range:
            # Guild must be within the range of snowflakes
            return self.in_range(guild.id, options.min_id, options.max_id)
        elif type == ExperimentFilterType.member_count_range:
            # Guild must be within the range of member counts
            return guild.member_count is not None and self.in_range(guild.member_count, options.min_id, options.max_id)
        elif type == ExperimentFilterType.ids:
            # Guild must be in the list of snowflakes, similar to ExperimentOverride
            return options.guild_ids is not None and guild.id in options.guild_ids
        elif type == ExperimentFilterType.hub_type:
            # TODO: Pending hub implementation
            # return guild.hub_type and options.guild_hub_types and guild.hub_type.value in options.guild_hub_types
            return False
        elif type == ExperimentFilterType.hash_range:
            # Guild must... no idea tbh
            # Probably for cleanly splitting populations
            result = murmurhash32(f'{options.hash_key}:{guild.id}', signed=False)
            if result > 0:
                result += result
            else:
                result = (result % 0x100000000) >> 0
            return options.target and result % 10000 < options.target
        elif type == ExperimentFilterType.vanity_url:
            # Guild must or must not have a vanity URL
            return bool(guild.vanity_url_code) == options.guild_has_vanity_url
        else:
            # TODO: Maybe just return False?
            raise NotImplementedError(f'Unknown filter type: {type}')


class ExperimentPopulation:
    """Represents a population of an experiment.

    .. container:: operations

        .. describe:: x in y

            Checks if a guild is present in the population.

    .. versionadded:: 2.1

    Attributes
    -----------
    experiment: :class:`GuildExperiment`
        The experiment this population belongs to.
    filters: List[:class:`ExperimentFilter`]
        The filters that apply to the population.
    rollouts: List[Tuple[:class:`int`, :class:`int`]]
        The position-based rollouts of the population.
    """

    __slots__ = ('experiment', 'filters', 'rollouts')

    def __init__(self, experiment: GuildExperiment, data: PopulationPayload):
        rollouts, filters = data

        self.experiment = experiment
        self.filters: List[ExperimentFilter] = [ExperimentFilter(self, x) for x in filters]
        self.rollouts: List[ExperimentRollout] = [ExperimentRollout(self, x) for x in rollouts]

    def __repr__(self) -> str:
        return f'<ExperimentPopulation experiment={self.experiment!r} filters={self.filters!r} rollouts={self.rollouts!r}>'

    def __contains__(self, item: Guild, /) -> bool:
        return self.bucket_for(item) != -1

    def bucket_for(self, guild: Guild, _result: Optional[int] = None, /) -> int:
        """Returns the assigned experiment bucket within a population for a guild.
        Defaults to none (-1) if the guild is not in the population.

        .. note::

            This function is not intended to be used directly. Instead, use :func:`GuildExperiment.bucket_for`.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to compute experiment eligibility for.

        Raises
        ------
        :exc:`ValueError`
            The experiment name is unset.

        Returns
        -------
        :class:`int`
            The experiment bucket.
        """
        if _result is None:
            _result = self.experiment.result_for(guild)

        for filter in self.filters:
            if not filter.is_eligible(guild):
                return -1

        for rollout in self.rollouts:
            for start, end in rollout.ranges:
                if start <= _result <= end:
                    return rollout.bucket

        return -1


class ExperimentOverride:
    """Represents an experiment override.

    .. container:: operations

        .. describe:: len(x)

            Returns the number of resources eligible for the override.

        .. describe:: x in y

            Checks if a resource is eligible for the override.

        .. describe:: iter(x)

            Returns an iterator of the resources eligible for the override.

    .. versionadded:: 2.1

    Attributes
    -----------
    experiment: :class:`GuildExperiment`
        The experiment this override belongs to.
    bucket: :class:`int`
        The bucket the override applies.
    """

    __slots__ = ('experiment', 'bucket', '_ids')

    def __init__(self, experiment: GuildExperiment, data: OverridePayload):
        self.experiment = experiment
        self.bucket: int = data['b']
        self._ids: SnowflakeList = SnowflakeList(map(int, data['k']))

    def __repr__(self) -> str:
        return f'<ExperimentOverride bucket={self.bucket} ids={self.ids!r}>'

    def __len__(self) -> int:
        return len(self._ids)

    def __contains__(self, item: Union[int, Snowflake], /) -> bool:
        return getattr(item, 'id', item) in self._ids

    def __iter__(self) -> Iterator[int]:
        return iter(self._ids)

    @property
    def ids(self) -> Sequence[int]:
        """Sequence[:class:`int`]: The eligible guild/user IDs for the override."""
        return SequenceProxy(self._ids)


class HoldoutExperiment:
    """Represents an experiment dependency.

    .. container:: operations

        .. describe:: x in y

            Checks if a guild fulfills the dependency.

    .. versionadded:: 2.1

    Attributes
    -----------
    dependent: :class:`GuildExperiment`
        The experiment that depends on this experiment.
    name: :class:`str`
        The name of the dependency.
    bucket: :class:`int`
        The required bucket of the dependency.
    """

    __slots__ = ('dependent', 'name', 'bucket')

    def __init__(self, dependent: GuildExperiment, name: str, bucket: int):
        self.dependent = dependent
        self.name: str = name
        self.bucket: int = bucket

    def __repr__(self) -> str:
        return f'<HoldoutExperiment dependent={self.dependent!r} name={self.name!r} bucket={self.bucket}>'

    def __contains__(self, item: Guild) -> bool:
        return self.is_eligible(item)

    @property
    def experiment(self) -> Optional[GuildExperiment]:
        """Optional[:class:`GuildExperiment`]: The experiment dependency, if found."""
        experiment_hash = murmurhash32(self.name, signed=False)
        experiment = self.dependent._state.guild_experiments.get(experiment_hash)
        if experiment and not experiment.name:
            # Backfill the name
            experiment._name = self.name
        return experiment

    def is_eligible(self, guild: Guild, /) -> bool:
        """Checks whether the guild fulfills the dependency.

        .. note::

            This function is not intended to be used directly. Instead, use :func:`GuildExperiment.bucket_for`.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to check.

        Returns
        --------
        :class:`bool`
            Whether the guild fulfills the dependency.
        """
        experiment = self.experiment
        if experiment is None:
            # We don't have the experiment, so we can't check
            return True

        return experiment.bucket_for(guild) == self.bucket


class GuildExperiment:
    """Represents a guild experiment rollout.

    .. container:: operations

        .. describe:: x == y

            Checks if two experiments are equal.

        .. describe:: x != y

            Checks if two experiments are not equal.

        .. describe:: hash(x)

            Returns the experiment's hash.

    .. versionadded:: 2.1

    Attributes
    -----------
    hash: :class:`int`
        The 32-bit unsigned Murmur3 hash of the experiment's name.
    revision: :class:`int`
        The current revision of the experiment rollout.
    populations: List[:class:`ExperimentPopulation`]
        The rollout populations of the experiment.
    overrides: List[:class:`ExperimentOverride`]
        The explicit bucket overrides of the experiment.
    overrides_formatted: List[List[:class:`ExperimentPopulation`]]
        Additional rollout populations for the experiment.
    holdout: Optional[:class:`HoldoutExperiment`]
        The experiment this experiment depends on, if any.
    aa_mode: :class:`bool`
        Whether the experiment is in A/A mode.
    """

    __slots__ = (
        '_state',
        'hash',
        '_name',
        'revision',
        'populations',
        'overrides',
        'overrides_formatted',
        'holdout',
        'aa_mode',
    )

    def __init__(self, *, state: ConnectionState, data: GuildExperimentPayload):
        (
            hash,
            hash_key,
            revision,
            populations,
            overrides,
            overrides_formatted,
            holdout_name,
            holdout_bucket,
            aa_mode,
        ) = data

        self._state = state
        self.hash: int = hash
        self._name: Optional[str] = hash_key
        self.revision: int = revision
        self.populations: List[ExperimentPopulation] = [ExperimentPopulation(self, x) for x in populations]
        self.overrides: List[ExperimentOverride] = [ExperimentOverride(self, x) for x in overrides]
        self.overrides_formatted: List[List[ExperimentPopulation]] = [
            [ExperimentPopulation(self, y) for y in x] for x in overrides_formatted
        ]
        self.holdout: Optional[HoldoutExperiment] = (
            HoldoutExperiment(self, holdout_name, holdout_bucket)
            if holdout_name is not None and holdout_bucket is not None
            else None
        )
        self.aa_mode: bool = aa_mode == 1

    def __repr__(self) -> str:
        return f'<GuildExperiment hash={self.hash}{f" name={self._name!r}" if self._name else ""}>'

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, GuildExperiment):
            return self.hash == other.hash
        return NotImplemented

    @property
    def name(self) -> Optional[str]:
        """Optional[:class:`str`]: The unique name of the experiment.

        This data is not always available via the API, and must be set manually for using related functions.
        """
        return self._name

    @name.setter
    def name(self, value: Optional[str], /) -> None:
        if not value:
            self._name = None
        elif murmurhash32(value, signed=False) != self.hash:
            raise ValueError('The name provided does not match the experiment hash')
        else:
            self._name = value

    def result_for(self, guild: Snowflake, /) -> int:
        """Returns the calulated position of the guild within the experiment (0-9999).

        Parameters
        -----------
        guild: :class:`abc.Snowflake`
            The guild to compute the position for.

        Raises
        ------
        :exc:`ValueError`
            The experiment name is unset.

        Returns
        -------
        :class:`int`
            The position of the guild within the experiment.
        """
        if not self.name:
            raise ValueError('The experiment name must be set to compute the result')

        return murmurhash32(f'{self.name}:{guild.id}', signed=False) % 10000

    def bucket_for(self, guild: Guild, /) -> int:
        """Returns the assigned experiment bucket for a guild.
        Defaults to none (-1) if the guild is not in the experiment.

        Parameters
        -----------
        guild: :class:`Guild`
            The guild to compute experiment eligibility for.

        Raises
        ------
        :exc:`ValueError`
            The experiment name is unset.

        Returns
        -------
        :class:`int`
            The experiment bucket.
        """
        # a/a mode is always -1
        if self.aa_mode:
            return -1

        # Holdout must be fulfilled
        if self.holdout and not self.holdout.is_eligible(guild):
            return -1

        hash_result = self.result_for(guild)

        # Overrides take precedence
        # And yes, they can be assigned to a user ID
        for override in self.overrides:
            if guild.id in override.ids or guild.owner_id in override.ids:
                return override.bucket

        for overrides in self.overrides_formatted:
            for override in overrides:
                pop_bucket = override.bucket_for(guild, hash_result)
                if pop_bucket != -1:
                    return pop_bucket

        for population in self.populations:
            pop_bucket = population.bucket_for(guild, hash_result)
            if pop_bucket != -1:
                return pop_bucket

        return -1

    def guilds_for(self, bucket: int, /) -> List[Guild]:
        """Returns a list of guilds assigned to a specific bucket.

        Parameters
        -----------
        bucket: :class:`int`
            The bucket to get guilds for.

        Raises
        ------
        :exc:`ValueError`
            The experiment name is unset.

        Returns
        -------
        List[:class:`Guild`]
            The guilds assigned to the bucket.
        """
        return [x for x in self._state.guilds if self.bucket_for(x) == bucket]


class UserExperiment:
    """Represents a user's experiment assignment.

    .. container:: operations

        .. describe:: x == y

            Checks if two experiments are equal.

        .. describe:: x != y

            Checks if two experiments are not equal.

        .. describe:: hash(x)

            Returns the experiment's hash.

    .. versionadded:: 2.1

    .. note::

        In contrast to the wide range of data provided for guild experiments,
        user experiments do not reveal detailed rollout information, providing only the assigned bucket.

    Attributes
    ----------
    hash: :class:`int`
        The 32-bit unsigned Murmur3 hash of the experiment's name.
    revision: :class:`int`
        The current revision of the experiment rollout.
    assignment: :class:`int`
        The assigned bucket for the user.
    override: :class:`int`
        The overriden bucket for the user, takes precedence over :attr:`assignment`.
    population: :class:`int`
        The internal population group for the user.
    aa_mode: :class:`bool`
        Whether the experiment is in A/A mode.
    """

    __slots__ = (
        '_state',
        '_name',
        'hash',
        'revision',
        'assignment',
        'override',
        'population',
        '_result',
        'aa_mode',
    )

    def __init__(self, *, state: ConnectionState, data: AssignmentPayload):
        (hash, revision, bucket, override, population, hash_result, aa_mode) = data

        self._state = state
        self._name: Optional[str] = None
        self.hash: int = hash
        self.revision: int = revision
        self.assignment: int = bucket
        self.override: int = override
        self.population: int = population
        self._result: int = hash_result
        self.aa_mode: bool = True if aa_mode == 1 else False

    def __repr__(self) -> str:
        return f'<UserExperiment hash={self.hash}{f" name={self._name!r}" if self._name else ""} bucket={self.bucket}>'

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, UserExperiment):
            return self.hash == other.hash
        return NotImplemented

    @property
    def name(self) -> Optional[str]:
        """Optional[:class:`str`]: The unique name of the experiment.

        This data is not always available via the API, and must be set manually for using related functions.
        """
        return self._name

    @name.setter
    def name(self, value: Optional[str], /) -> None:
        if not value:
            self._name = None
        elif murmurhash32(value, signed=False) != self.hash:
            raise ValueError('The name provided does not match the experiment hash')
        else:
            self._name = value

    @property
    def bucket(self) -> int:
        """:class:`int`: The assigned bucket for the user."""
        if self.aa_mode:
            return -1
        return self.override if self.override != -1 else self.population

    @property
    def result(self) -> int:
        """:class:`int`: The calulated position of the user within the experiment (0-9999).

        Raises
        ------
        :exc:`ValueError`
            The experiment name is unset without a precomputed result.
        """
        if self._result:
            return self._result
        elif not self.name:
            raise ValueError('The experiment name must be set to compute the result')
        else:
            return murmurhash32(f'{self.name}:{self._state.self_id}', signed=False) % 10000
