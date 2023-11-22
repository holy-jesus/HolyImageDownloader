import asyncio
from io import BytesIO
from typing import Tuple, Union
import imghdr

from aiohttp import ClientSession, ClientConnectionError
from PIL import Image as PILImage


class Image:
    def __init__(self, json: list, session: ClientSession) -> None:
        self.url: str = json["url"]
        self.width: int = json["width"]
        self.height: int = json["height"]
        self.size: tuple[int, int] = (json["width"], json["height"])
        self.session = session

    def __repr__(self) -> str:
        return f"Image(url={self.url}, size={self.width}x{self.height})"

    def _resize_reformat_picture(self, image: bytes, new_size: Tuple[int, int] = None):
        im = PILImage.open(BytesIO(image))
        if new_size:
            im = im.resize(new_size)
        buffered = BytesIO()
        im.save(buffered, im.format)
        return buffered.getvalue(), im.format.lower()

    def to_dict(self):
        return {"url": self.url, "size": self.size}

    async def download(
        self,
        new_size: Tuple[int, int] = None,
    ) -> Union[Tuple[bytes, str], Tuple[None, None]]:
        try:
            response = await self.session.get(self.url, timeout=10)
            if "image" not in response.headers.get("Content-Type", ""):
                return None, None
            content = await response.content.read()
            if new_size:
                content, format = await asyncio.to_thread(
                    self._resize_reformat_picture,
                    content,
                    new_size,
                )
            else:
                format = imghdr.what(None, content)
                if format is None:
                    return None, None
            return content, format
        except ClientConnectionError:
            return None, None
        except TimeoutError:
            return None, None
