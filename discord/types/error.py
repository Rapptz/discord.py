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

from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired


class FormError(TypedDict):
    code: str
    message: str


class FormErrorWrapper(TypedDict):
    _errors: List[FormError]


FormErrors = Union[FormErrorWrapper, Dict[str, 'FormErrors']]


class Error(TypedDict):
    code: int
    message: str
    errors: NotRequired[FormErrors]


CaptchaService = Literal['hcaptcha', 'recaptcha']


class CaptchaRequired(TypedDict):
    captcha_key: List[str]
    captcha_service: CaptchaService
    captcha_sitekey: Optional[str]
    captcha_rqdata: NotRequired[str]
    captcha_rqtoken: NotRequired[str]
