import asyncio
from io import BytesIO
import imghdr

from aiohttp import ClientSession, ClientConnectionError
import filetype
from PIL import Image as PILImage
from PIL import UnidentifiedImageError


class Image:
    def __init__(self, json: list, session: ClientSession) -> None:
        self.url: str = json["url"]
        self.width: int = json["width"]
        self.height: int = json["height"]
        self.size: tuple[int, int] = (json["width"], json["height"])
        self.session = session

    def __repr__(self) -> str:
        return f"Image(url={self.url}, size={self.width}x{self.height})"

    def _resize_reformat_picture(
        self,
        image: bytes,
        new_size: tuple[int, int] | None = None,
        new_format: str | None = None,
    ) -> tuple[bytes, str] | tuple[None, None]:
        MAINTAIN_ASPECT_RATION = True
        try:
            im = PILImage.open(BytesIO(image))
        except UnidentifiedImageError:
            return None, None
        if new_size and MAINTAIN_ASPECT_RATION:
            im.thumbnail(new_size)
        elif new_size:
            im = im.resize(new_size)
        buffered = BytesIO()
        im.save(buffered, new_format or im.format)
        return buffered.getvalue(), im.format.lower()

    def to_dict(self):
        return {"url": self.url, "size": self.size}

    async def download(
        self, new_size: tuple[int, int] | None = None, new_format: str | None = None
    ) -> tuple[bytes, str] | tuple[None, None]:
        try:
            async with self.session.get(self.url, timeout=10) as response:
                content = await response.content.read()
                if new_size:
                    content, format = await asyncio.to_thread(
                        self._resize_reformat_picture,
                        content,
                        new_size,
                        new_format,
                    )
                else:
                    format = filetype.guess_extension(content)
                    if format is None:
                        return None, None
                return content, format
        except ClientConnectionError:
            return None, None
        except TimeoutError:
            return None, None
