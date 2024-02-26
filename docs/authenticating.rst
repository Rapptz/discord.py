:orphan:

.. _authenticating:

Authenticating
==============

Tokens
-------

Tokens are how we authenticate with Discord. User accounts use the same token system as bots, received after authenticating with the Discord API.

They follow this format:

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

How do I obtain mine?
----------------------
The library does not yet support authenticating traditionally, so you will have to obtain your token manually.

To obtain your token from the Discord client, the easiest way is pasting this into the developer console (CTRL+SHIFT+I):

.. code:: js

    (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m => m?.exports?.default?.getToken).exports.default.getToken()


Or, you can do it manually:

1. Open developer tools (CTRL+SHIFT+I).
2. Click the Network tab.
3. Click the XHR tab.
4. Select a request and click the Headers tab.
5. Copy-paste the value in the Authorization header.
