async def limited_task(semaphore, coroutine):
    async with semaphore:
        return await coroutine
