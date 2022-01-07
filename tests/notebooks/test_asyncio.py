import asyncio


async def f(x):
    print(f"F({x})")
    return x + 3


def blocking(x):
    return asyncio.run(f(x))


def nonblocking(x):
    async def inner():
        await f(x)

    asyncio.ensure_future(inner())


y = asyncio.run(f(2))
print(y)

print(blocking(3))
print(nonblocking(4))

# asyncio.get_event_loop().
# asyncio.ensure_future(f(11))


import time

time.sleep(10)
print("DONE")
