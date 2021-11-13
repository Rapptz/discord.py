.. currentmodule:: discord

.. _migrating:

Migrating to this library
==========================

| This library is designed to be compatible with discord.py.
| However, the user and bot APIs are *not* the same.

Most things bots can do, users can (in some capacity) as well.

However, a number of things have been removed.
For example:

- `Intents`: While the gateway technically accepts Intents for user accounts (and even modifies payloads to be a little more like bot payloads), it leads to breakage. Additionally, it's a giant waving red flag to Discord.
- `Shards`: The concept doesn't exist and is unneeded for users.
- `Guild.fetch_members`: The `/guilds/:id/members` and `/guilds/:id/members/search` endpoints instantly phone-lock your account. For more information about guild members, please read their respective section below.

Additionally, existing payloads and headers have been heavily changed to match the Discord client.

Guild Members
--------------
| Since the concept of Intents (mostly) doesn't exist for user accounts; you just get all events, right?
| Well, yes but actually no.

For 80% of things, events are identical to bot events. However, other than the quite large amount of new events, not all events work the same.

The biggest example of this are the events `on_member_add`, `on_member_update`/`on_user_update`, and `on_member_remove`.

Bots
~~~~~
| For bots (with the member intent), it's simple.
| They request all guild members with an OPCode 8 (chunk the guild), and receive respective `GUILD_MEMBER_*` events, that are then parsed by the library and dispatched to users.
| If the bot has the presence intent, it even gets an initial member cache in the `GUILD_CREATE` event.

Users
~~~~~~
| Users, however, do not work like this.
| If you have one of kick members, ban members, or manage roles, you can request all guild members the same way bots do. The client uses this in various areas of guild settings.

| But, here's the twist: users do not receive `GUILD_MEMBER_*` reliably.
| They receive them in certain circumstances, but they're usually rare and nothing to be relied on.
| If the Discord client ever needs member objects for specific users, it sends an OPCode 8 with the specific user IDs/names.
This is why this is recommended if you want to fetch specific members (implemented as :func:`Guild.query_members` in the library).
The client almost never uses the :func:`Guild.fetch_member` endpoint.
| However, the maximum amount of members you can get with this method is 100 per request.

But, you may be thinking, how does the member list work? Why can't you just utilize that? This is where it gets complicated.
First, let's make sure we understand a few things:

- The API doesn't differentiate between offline and invisible members (for a good reason).
- The concept of a member list is not per-guild, it's per-channel. This makes sense if you think about it, since the member list only shows users that have access to a specific channel.
- The member list is always up-to-date.
- If a server has >1k members, the member list does **not** have offline members.

The member list uses OPCode 14, and the `GUILD_MEMBER_LIST_UPDATE` event.

| One more thing you need to understand, is that the member list is lazily loaded.
You subscribe to 100 member ranges, and can subscribe to 2 per-request (needs more testing).
So, to subscribe to all available ranges, you need to spam the gateway quite a bit (especially for large guilds).
| Once you subscribe to a range, you'll receive `GUILD_MEMBER_LIST_UPDATE`s for it whenever someone is added to it (i.e. someone joined the guild, changed their nickname so they moved in the member list alphabetically, came online, etc.), removed from it (i.e. someone left the guild, went offline, changed their nickname so they moved in the member list alphabetically), or updated in it (i.e. someone got their roles changed, or changed their nickname but remained in the same range).
| These can be parsed and dispatched as `on_member_add`, `on_member_update`/`on_user_update`, and `on_member_remove`.

You may have already noticed a few problems with this:

1. You'll get spammed with `member_add/remove`s whenever someone changes ranges.
2. For guilds with >1k members you don't receive offline members. So, you won't know if an offline member is kicked, or an invisible member joins/leaves. You also won't know if someone came online or joined. Or, if someone went offline or left.

| #1 is solveable with a bit of parsing, but #2 is a huge problem.
| If you have the permissions to request all guild members, you can combine that with member list scraping and get a *decent* local member cache.
However, because of the nature of this (and the fact that you'll have to request all guild membesr again every so often), accurate events are nearly impossible.

Additionally, there are more caveats:

1. `GUILD_MEMBER_LIST_UPDATE` removes provide an index, not a user ID. The index starts at 0 from the top of the member list and includes hoisted roles.
2. For large servers, you get ratelimited pretty fast, so scraping can take over half an hour.
3. The scraping has to happen every time the bot starts. This not only slows things down, but *may* make Discord suspicious.
4. Remember that member lists are per-channel? Well, that means you can only subscribe all members that can *see* the channel you're subscribing too.

#1 is again solveable with a bit of parsing. There's not much you can do about #2 and #3. But, to solve #4, you *can* subscribe to multiple channels. Although, that will probably have problems of its own.

There are a few more pieces of the puzzle:

- There is a `/guilds/:id/roles/:id/member-ids` endpoint that provides up to 100 member IDs for any role other than the default role. You can use :func:`Guild.query_members` to fetch all these members in one go.
- With OPCode 14, you can subscribe to certain member IDs and receive presence updates for them. The limit of IDs per-request is currently unknown, but I have witnessed the client send over 200/request. This may help with the offline members issue.
- Thread member lists do *not* work the same. You just send an OPCode 14 with the thread IDs and receive a `THREAD_MEMBER_LIST_UPDATE` with all the members. The cache then stays updated with `GUILD_MEMBER_UPDATE` and `THREAD_MEMBERS_UPDATE` events.
- OPCode 14 lets you subscribe to multiple channels at once, and you *might* be able to do more than 2 ranges at once.
