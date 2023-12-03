import asyncio
from pathlib import Path
from io import BytesIO

# from rich import print
import aiofiles
from aiohttp import ClientSession, ClientConnectionError
import filetype
from PIL import Image as PILImage, UnidentifiedImageError

try:
    from result import Result
    from image import Image
    from config import HEADERS
except ImportError:
    from .result import Result
    from .image import Image
    from .config import HEADERS


class Downloader:
    def __init__(
        self,
        results: list[Result],
        path: Path,
        session: ClientSession,
        downloaders: int = 10,
        new_size: tuple[int, int] | None = None,
        new_format: str | None = None,
        maintain_aspect_ratio: bool = True
    ) -> None:
        self.queue = asyncio.Queue()
        self.path: Path = path
        self.total = len(results)
        self.downloaded = 0
        self.results = results
        self.session = session
        self._downloaders = downloaders
        self.new_size = new_size
        self.new_format = new_format
        self.maintain_aspect_ratio = maintain_aspect_ratio

    async def download(self):
        loop = asyncio.get_event_loop()
        tasks: list[asyncio.Task] = []
        for filename, result in enumerate(self.results):
            await self.queue.put((result, str(filename)))
        for _ in range(self._downloaders):
            tasks.append(loop.create_task(self._downloader()))
        await self.queue.join()
        for task in tasks:
            task.cancel()

    async def _downloader(self):
        while True:
            result, filename = await self.queue.get()
            content, format = await self._download(result.image)
            if content is None:
                content, format = await self._download(result.preview)
                if content is None:
                    self.queue.task_done()
                    self.downloaded += 1
                    continue
            async with aiofiles.open(
                f"{self.path.absolute()}/{filename}.{format}", "wb"
            ) as file:
                await file.write(content)
            self.queue.task_done()
            self.downloaded += 1

    def _resize_reformat_picture(
        self,
        image: bytes,
    ) -> tuple[bytes, str] | tuple[None, None]:
        try:
            im = PILImage.open(BytesIO(image))
        except UnidentifiedImageError:
            return None, None
        if self.new_size and self.maintain_aspect_ratio:
            im.thumbnail(self.new_size)
        elif self.new_size:
            im = im.resize(self.new_size)
        buffered = BytesIO()
        if self.new_format:
            im.convert("RGB").save(buffered, self.new_format)
        else:
            im.save(buffered, im.format)
        return buffered.getvalue(), self.new_format or im.format.lower() 

    async def _download(
        self,
        image: Image,
    ) -> tuple[bytes, str] | tuple[None, None]:
        try:
            async with self.session.get(
                image.url, timeout=5, headers=HEADERS
            ) as response:
                content = await response.content.read()
                if self.new_size or self.new_format:
                    try:
                        content, format = await asyncio.to_thread(
                            self._resize_reformat_picture, content
                        )
                    except Exception as e:
                        # print(e)
                        return None, None
                else:
                    format = filetype.guess_extension(content)
                    if format is None:
                        return None, None
                return content, format
        except ClientConnectionError:
            return None, None
        except TimeoutError:
            return None, None
