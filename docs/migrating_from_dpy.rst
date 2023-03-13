.. currentmodule:: discord

.. _migrating_from_dpy:

Migrating to This Library
==========================

| This library is designed to be compatible with discord.py.
| However, the user and bot APIs are *not* the same.

Most things bots can do, users can (in some capacity) as well. The biggest difference is the amount of added things: users can do a lot more things than bots can.

However, a number of things have been removed.
For example:

- ``Intents``: While the gateway technically accepts intents for user accounts, it can break things and is a giant waving red flag to Discord.
- ``Shards``: Again, technically accepted but useless.
- ``discord.ui``: Users cannot utilize the bot UI kit.
- ``discord.app_commands``: Users cannot register application commands.

Additionally, existing payloads and headers have been changed to match the Discord client.

Guild members
--------------
| Since the concept of Intents (mostly) doesn't exist for user accounts; you just get all events, right?
| Well, yes but actually no.

For 80% of things, events are identical to bot events. However, other than the quite large amount of new events, not all events work the same.

The biggest example of this are the events ``on_member_add``, ``on_member_update``\/``on_user_update``, ``on_member_remove``, and ``on_presence_update``.

(If you're just looking for the implementation, skip to the bottom of this section.)

Bots
~~~~~
For bots (with the member intent), it's simple.

They request all guild members with an OPCode 8 (chunk the guild), and receive respective ``GUILD_MEMBER_*`` events, that are then parsed by the library and dispatched to users.

If the bot has the presence intent, it even gets an initial member cache in the ``GUILD_CREATE`` event and receives ``PRESENCE_UPDATE``.

Users
~~~~~~
| Users, however, do not work like this.
| If you have one of kick members, ban members, or manage roles, you can request all guild members the same way bots do. The client uses this in various areas of guild settings.

| But, here's the twist: users do not receive ``GUILD_MEMBER_*`` reliably.
| They receive them in certain circumstances (such as when subscribing to updates for specific users), but they're usually rare and nothing to be relied on.

If the Discord client ever needs member objects for specific users, it sends an OPCode 8 with the specific user IDs/names.
This is why this is recommended if you want to fetch specific members (implemented as :func:`Guild.query_members` in the library).

However, the maximum amount of members you can get with this method is 100 per request.

But, you may be thinking, how does the member sidebar work? Why can't you just utilize that? This is where it gets complicated.
First, let's make sure we understand a few things:

- The API doesn't differentiate between offline and invisible members (for a good reason).
- The concept of a member sidebar is not per-guild, it's per-channel. This makes sense if you think about it, since the member sidebar only shows users that have access to a specific channel. Member lists have IDs that can be calculated from channel permission overwrites to find unique member lists.
- If a server has >1,000 members, the member sidebar does **not** have offline members.

The member sidebar uses OPCode 14 and the ``GUILD_MEMBER_LIST_UPDATE`` event.

One more thing you need to understand, is that the member sidebar is lazily loaded.
You usually subscribe to 100 member ranges, and can subscribe to 5 per-channel per-request (up to 5 channels a request).
If the guild's member count has never been above 75,000 members, you can subscribe to 400 member ranges instead.

So, to subscribe to all available ranges, you need to spam the gateway quite a bit (especially for large guilds).
Additionally, while you can subscribe to 5 channels/request, the channels need to have the same permissions, or you'll be subscribing to two different lists (not ideal).

| Once you subscribe to a range, you'll receive ``GUILD_MEMBER_LIST_UPDATE`` s for it whenever someone is added to it (i.e. someone joined the guild, changed their nickname so they moved in the member list alphabetically, came online, etc.), removed from it (i.e. someone left the guild, went offline, changed their nickname so they moved in the member sidebar alphabetically), or updated in it (i.e. someone got their roles changed, or changed their nickname but remained in the same position).
| These can be parsed and dispatched as ``on_member_add``, ``on_member_update``\/``on_user_update``, ``on_member_remove``, and ``on_presence_update``.

You may have already noticed a few problems with this:

1. You'll get spammed with ``member_add/remove`` s whenever someone changes position in the member sidebar.
2. For guilds with >1,000 members, you don't receive offline members. So, you won't know if an offline member is kicked, or an invisible member joins/leaves. You also won't know if someone came online or joined. Or, if someone went offline or left.

| #1 is mostly solveable with a bit of parsing, but #2 is a huge problem.
| If you have the permissions to request all guild members, you can combine that with member sidebar scraping and get a *decent* local member cache. However, because of the nature of this (and the fact that you'll have to request all guild membesr again every so often), accurate events are nearly impossible.

Additionally, there are more caveats:

1. ``GUILD_MEMBER_LIST_UPDATE`` removes provide an index, not a user ID. The index starts at 0 from the top of the member sidebar and includes hoisted roles.
2. You get ratelimited pretty fast, so scraping can take minutes for extremely large guilds.
3. The scraping has to happen every time the bot starts. This not only slows things down, but *may* make Discord suspicious.
4. Remember that member sidebars are per-channel? Well, that means you can only subscribe all members that can *see* the channel(s) you're subscribing too.

#1 is again solveable with a bit of parsing. There's not much you can do about #2 and #3. But, to solve #4, you *can* subscribe to multiple channels (which has problems of its own and makes events virtually impossible).

There are a few more pieces of the puzzle:

- There is a ``/guilds/:id/roles/:id/member-ids`` endpoint that provides up to 100 member IDs for any role other than the default role. You can use :func:`Guild.query_members` to fetch all these members in one go.
- With OPCode 14, you can subscribe to certain member IDs and receive member/presence updates for them. There is no limit to the amount of IDs you can subscribe to (except for the gateway payload size limit).
- Thread member sidebars do *not* work the same. You just send an OPCode 14 with the thread IDs and receive a ``THREAD_MEMBER_LIST_UPDATE`` with all the members. The cache then stays updated with ``GUILD_MEMBER_UPDATE`` and ``THREAD_MEMBERS_UPDATE`` events.

Implementation
~~~~~~~~~~~~~~~
The library offers two avenues to get the "entire" member list of a guild.

- :func:`Guild.chunk`: If a guild has less than 1,000 members, and has at least one channel that everyone can view, you can use this method to fetch the entire member list by scraping the member sidebar. With this method, you also get events.
- :func:`Guild.fetch_members`: If you have the permissions to request all guild members, you can use this method to fetch the entire member list. Else, this method scrapes the member sidebar (which can become very slow), this only returns online members if the guild has more than 1,000 members. This method does not get events.
