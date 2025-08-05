async def limited_task(coro, semaphore):
    async with semaphore:
        return await coro
