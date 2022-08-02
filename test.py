from discord.ext import tasks




@tasks.loop()
async def foo(a: int) -> str:
    ...

@foo.error
async def foo_error(e: BaseException) -> None:
    ...


class Foo:

    @tasks.loop()
    async def foo(self, a: int) -> str:
        ...

    @foo.error
    async def foo_error(self, e: BaseException) -> None:
        ...


reveal_type(foo)
reveal_type(foo.coro)
reveal_type(foo_error)

reveal_type(Foo.foo)
reveal_type(Foo.foo.coro)
reveal_type(Foo().foo_error)

