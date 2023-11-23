from typing import Tuple, List
import asyncio
from pathlib import Path

from aiohttp import ClientSession
import aiofiles

try:
    from result import Result
except ModuleNotFoundError:
    from .result import Result

class Batch:
    def __init__(self, results: dict, session: ClientSession) -> None:
        self.results: Tuple[Result] = tuple(
            Result(result, session) for result in results
        )
        self.session = session

    def __len__(self):
        return len(self.results)

    def to_dict(self):
        return {"data": [result.to_dict() for result in self.results]}

    async def _downloader(
        self,
        queue: asyncio.Queue,
        path_to_save: str,
        new_size: Tuple[int, int] = None,
    ):
        while True:
            result_number: int = await queue.get()
            filename = str(image)
            image = self.results[result_number].image
            content, format = await image.download(new_size)
            if content is None:
                preview = self.results[result_number].preview
                content, format = await preview.download(new_size)
                if content is None:
                    queue.task_done()
                    continue
            async with aiofiles.open(
                f"{path_to_save}/{filename}.{format}", "wb"
            ) as file:
                await file.write(content)
            queue.task_done()

    async def download(
        self,
        path_to_save: str = None,
        number_of_downloaders: int = None,
        new_size: Tuple[int, int] = None,
    ) -> None:
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        if not number_of_downloaders:
            number_of_downloaders = 10
        elif number_of_downloaders == -1:
            number_of_downloaders = len(self.results)
        for result in range(len(self.results)):
            await queue.put(result)
        tasks: List[asyncio.Task] = []
        for _ in range(number_of_downloaders):
            tasks.append(
                loop.create_task(self._downloader(queue, path_to_save, new_size))
            )
        await queue.join()
        for task in tasks:
            task.cancel()
