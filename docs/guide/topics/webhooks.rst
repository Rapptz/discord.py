.. currentmodule:: discord

.. _guide_webhooks:

Webhooks
========

Webhooks are used for posting messages in Discord text channels without relying on a bot user.

The focus of this section is to provide a basic understanding of webhooks and
working with them using discord.py.

For detailed information about webhooks, See the API reference for :class:`Webhook` class.


Introduction to webhooks
~~~~~~~~~~~~~~~~~~~~~~~~

The difference between sending messages with webhooks and bots is that latter requires
proper authentication and a bot user while the former neither requires bot user nor
authentication.

There are currently three types of webhooks:

1. Incoming webhooks
2. Channel follower webhooks
3. Application webhooks

**Incoming webhooks** are associated to a channel and can post messages in that channel
using a webhook token.

**Channel follower webhooks** are used for crossposting of messages in news channels
by Discord. This type does not have any token associated to it and bots cannot post
messages through these webhooks.

**Application webhooks** are used for creating interaction responses. The management of
this type of webhooks are handled internally by the library and is not in scope of this guide.

This guide will primarily focus on the first type i.e Incoming webhooks.

