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

from typing import List, Literal, Optional, Tuple, TypedDict, Union

from typing_extensions import NotRequired


class ExperimentResponse(TypedDict):
    fingerprint: NotRequired[str]
    assignments: List[UserExperiment]


class ExperimentResponseWithGuild(ExperimentResponse):
    guild_experiments: NotRequired[List[GuildExperiment]]


class RolloutData(TypedDict):
    s: int
    e: int


Rollout = Tuple[int, List[RolloutData]]


Filters = List[
    Union[
        Tuple[Literal[1604612045], Tuple[Tuple[Literal[1183251248], List[str]]]],  # FEATURE
        Tuple[
            Literal[2404720969], Tuple[Tuple[Literal[3399957344], Optional[int]], Tuple[Literal[1238858341], int]]
        ],  # ID_RANGE
        Tuple[
            Literal[2918402255], Tuple[Tuple[Literal[3399957344], Optional[int]], Tuple[Literal[1238858341], int]]
        ],  # MEMBER_COUNT_RANGE
        Tuple[Literal[3013771838], Tuple[Tuple[Literal[3013771838], List[int]]]],  # IDs
        Tuple[Literal[4148745523], Tuple[Tuple[Literal[4148745523], List[int]]]],  # HUB_TYPE
        Tuple[Literal[188952590], Tuple[Tuple[Literal[188952590], bool]]],  # VANITY_URL
        Tuple[Literal[2294888943], Tuple[Tuple[Literal[2690752156], int], Tuple[Literal[1982804121], int]]],  # RANGE_BY_HASH
    ]
]


Population = Tuple[
    List[Rollout],  # rollouts
    Filters,  # filters
]


class Override(TypedDict):
    b: int
    k: List[int]


Holdout = Tuple[
    int,  # bucket
    str,  # experiment_name
]


UserExperiment = Tuple[
    int,  # hash
    int,  # revision
    int,  # bucket
    int,  # override
    int,  # population
    int,  # hash_result
    Literal[0, 1],  # aa_mode
    Literal[0, 1],  # trigger_debugging
]


GuildExperiment = Tuple[
    int,  # hash
    Optional[str],  # hash_key
    int,  # revision
    List[Population],  # populations
    List[Override],  # overrides
    List[List[Population]],  # overrides_formatted
    Optional[str],  # holdout_name
    Optional[int],  # holdout_bucket
    Literal[0, 1],  # aa_mode
    Literal[0, 1],  # trigger_debugging
]
