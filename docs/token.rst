:orphan:

.. versionadded:: 2.0
.. _tokens:

Tokens
=======

Tokens are how we authenticate with Discord.

Regular (and bot) tokens have this format:

.. image:: /images/token.png

MFA tokens, however, are just the HMAC prefixed with `mfa.` (as far as I know).

How do I obtain mine?
----------------------
To obtain your token from the Discord client, the easiest way is as follows:

1. Open developer tools (CTRL+SHIFT+I).
2. Click the Network tab.
3. Click the XHR tab.
4. Select a request and click the Headers tab.
5. Copy-paste the value in the Authorization header.
