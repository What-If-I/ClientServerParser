import asyncio
import aiohttp

async def func():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.github.com/events') as resp:
            print(resp.status)
            print(await resp.text())


loop = asyncio.get_event_loop()
cor = loop.run_until_complete(func())
