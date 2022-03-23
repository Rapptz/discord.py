:orphan:

.. _tokens:

Tokens
=======

Tokens are how we authenticate with Discord.

Regular (and bot) tokens have this format:

.. list-table:: Discord Token
    :header-rows: 1

    * -
      - MjQ1NTU5MDg3NTI0MjE2ODMy
      - DulyxA
      - brcD2xRAqjACTuMcGPwy4TWVQdg
    * - **Decode**
      - :func:`base64.b64decode`
      - :func:`base64.b64decode` + 1293840000
      - N/A
    * - **Output**
      - User ID
      - Unix TS
      - HMAC


MFA tokens, however, are just the HMAC prefixed with **mfa.**

How do I obtain mine?
----------------------
To obtain your token from the Discord client, the easiest way is as follows:

1. Open developer tools (CTRL+SHIFT+I).
2. Click the Network tab.
3. Click the XHR tab.
4. Select a request and click the Headers tab.
5. Copy-paste the value in the Authorization header.
