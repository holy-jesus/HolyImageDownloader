import asyncio
import ctypes
import codecs
import re
import os
import locale
import json
from datetime import datetime
from random import choice, randint
from typing import AsyncGenerator, Tuple
from urllib.parse import quote_plus
from pathlib import Path

import aiohttp
import json5
from bs4 import BeautifulSoup
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from HolyImageDownloader.searchinfo import SearchInfo
from HolyImageDownloader.batch import Batch
from HolyImageDownloader.ENUMS import Color, Size, Time, Type, UsageRights, SafeSearch
from HolyImageDownloader.config import HEADERS, URL
from HolyImageDownloader.downloader import Downloader

console = Console()
_type = type


class ImageDownloader:
    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        self.session: aiohttp.ClientSession = session
        self.headers = HEADERS

    def __del__(self):
        # asyncio.get_event_loop().create_task(self.session.close())
        pass

    def search(
        self,
        search_query: str,
        safe_search: SafeSearch = SafeSearch.FILTER,
        size: Size = None,
        color: Color = None,
        type: Type = None,
        time: Time = None,
        usage_rights: UsageRights = None,
    ) -> AsyncGenerator[Batch, None]:
        if not search_query:
            raise ValueError("Search query can't be empty.")
        elif not isinstance(search_query, str):
            raise ValueError(
                f'Search query must be type "str", not "{_type(search_query)}"'
            )
        quoted_search_query = quote_plus(search_query)
        params = {"q": quoted_search_query, "oq": quoted_search_query, "gbv": "2"}
        tbs = ",".join(q.value for q in (size, color, type, time, usage_rights) if q)
        search_info = SearchInfo(
            search_query=search_query, safe_search=safe_search, tbs=tbs, params=params
        )
        return self._generator(search_info)

    async def _switch_safe_search(self, info: SearchInfo):
        response = await self._make_request("GET", URL.SAFESEARCH)
        content = await response.text()
        soup = BeautifulSoup(content, "lxml")
        attribute = {
            SafeSearch.FILTER: "data-setprefs-filter-url",
            SafeSearch.BLUR: "data-setprefs-blur-url",
            SafeSearch.OFF: "data-setprefs-off-url",
        }[info.safe_search]
        element = soup.find(attrs={attribute: True})
        url = URL.BASE + element[attribute]
        response = await self._make_request("GET", url)
        if response.status == 204:
            return True
        return False

    async def _generator(self, search_info: SearchInfo) -> AsyncGenerator[Batch, None]:
        response = await self._make_request(
            "GET",
            "https://www.google.com/search",
            {
                "as_st": "y",
                "tbm": "isch",
                "as_q": "hello world",
                "as_epq": "",
                "as_oq": "",
                "as_eq": "",
                "imgsz": "",
                "imgar": "",
                "imgc": "",
                "imgcolor": "",
                "imgtype": "",
                "cr": "",
                "as_sitesearch": "",
                "as_filetype": "",
                "tbs": "",
            },
        )
        content = await response.text()
        # with open("file", "w") as f:
        #     f.write(content)
        await self._parse_page(content, search_info)

        print(response.status)
        return
        await self._get_params(search_info)
        console.print("Got params")
        await self._switch_safe_search(search_info)
        console.print("Switched SafeSearch")
        print("&".join(f"{key}={value}" for key, value in search_info.params.items()))
        return
        response = await self._make_request(
            "GET", URL.SEARCH, params=search_info.params
        )
        content = await response.content.read()
        print(content)
        batch = self._parse_page(content, search_info)
        console.print(batch)
        yield batch
        while search_info.batchexecute_post is not None:
            response = await self.session.post(
                URL.BATCHEXECUTE,
                data=search_info.batchexecute_post,
                params=search_info.batchexecute_params,
                headers=self.headers,
            )
            content = await response.text()
            batch = self._parse_response(content, search_info)
            yield batch

    async def download(
        self,
        search_query: str,
        path: Path | str | None = None,
        safe_search: SafeSearch = SafeSearch.FILTER,
        max_images: int | None = None,
        size: Size | None = None,
        color: Color | None = None,
        type: Type | None = None,
        time: Time | None = None,
        usage_rights: UsageRights | None = None,
        number_of_downloaders: int | None = 50,
        new_size: Tuple[int, int] | None = None,
        new_format: str | None = None,
        maintain_aspect_ratio: bool = False,
    ):
        loop = asyncio.get_event_loop()
        max_images = max_images if max_images else -1
        if not path:
            path = Path().joinpath(f"./images/{search_query}/")
        elif isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        if not number_of_downloaders or number_of_downloaders <= 0:
            number_of_downloaders = 50
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Fetching images...", total=None)
            async for batch in self.search(
                search_query, safe_search, size, color, type, time, usage_rights
            ):
                results += batch.results
                progress.update(
                    task, description=f"Fetching images... {len(results)} fetched."
                )
                if max_images != -1 and len(results) > max_images:
                    break
        results = results[:max_images] if len(results) > max_images else results
        downloader = Downloader(
            results,
            path,
            self.session,
            number_of_downloaders,
            new_size,
            new_format,
            maintain_aspect_ratio,
            safe_search == SafeSearch.BLUR,
        )
        downloader_task = loop.create_task(downloader.download())
        with Progress() as progress:
            task = progress.add_task("[green]Downloading...", total=len(results))
            while not downloader_task.done():
                await asyncio.sleep(0.1)
                progress.update(task, completed=downloader.done)

    def _parse_AF_initDataCallback(self, AF_initDataCallback: dict, info: SearchInfo):
        if len(AF_initDataCallback[56]) < 2:
            # There are no images for this search query
            info.grid_state = None
            info.cursor = None
            info.batchexecute_post = None
            return None
        elif not AF_initDataCallback[56][1][0][-1][0][0]["444383007"][12][16]:
            # The pictures are over
            info.grid_state = None
            info.cursor = None
            info.batchexecute_post = None
        else:
            # elif AF_initDataCallback[56][1][0][-1][0][0]["444383007"][12][0] == "GRID_STATE0":
            batchexecute_data = AF_initDataCallback[56][1][0][-1][0][0]["444383007"][12]
            info.grid_state = batchexecute_data[11]
            info.cursor = (
                codecs.decode(batchexecute_data[16][3], "unicode_escape"),
                codecs.decode(batchexecute_data[16][4], "unicode_escape"),
            )
        results = []
        for result in AF_initDataCallback[56][1][0][-1][1][0]:
            if result[0][0]["444383007"][1] is None:
                continue
            result = result[0][0]["444383007"][1]
            if isinstance(result[21], dict):
                preview = {
                    "url": result[21][0],
                    "width": int(result[21][2]),
                    "height": int(result[21][1]),
                    "preview": True,
                }
                blurred = {
                    "url": result[2][0],
                    "width": int(result[2][2]),
                    "height": int(result[2][1]),
                    "preview": True,
                }
            else:
                preview = {
                    "url": result[2][0],
                    "width": int(result[2][2]),
                    "height": int(result[2][1]),
                    "preview": True,
                }
                blurred = None
            image = {
                "url": result[3][0],
                "width": int(result[3][2]),
                "height": int(result[3][1]),
                "preview": False,
            }
            website = {
                "url": result[25]["2003"][2],
                "base_url": result[25]["2003"][17],
                "title": result[25]["2003"][3],
                "name": result[25]["2003"][12],
            }
            results.append(
                {
                    "preview": preview,
                    "image": image,
                    "website": website,
                    "blurred": blurred,
                }
            )
        return results

    def _parse_page(self, content: str, info: SearchInfo) -> Batch | None:
        match = re.search(
            r"\{basecomb:'[^']+',basecss:'[^']+',basejs:'[^']+',excm:\[[^\]]+\]\}",
            content,
        )
        if not match:
            raise Exception("")  # TODO
        xjs = json5.loads(match.group())
        info.xjs = xjs
        print(xjs)
        return
        batch = None
        soup = BeautifulSoup(content, "lxml")
        for script in soup.select("script"):
            text = script.get_text()
            if "AF_initDataCallback({key: 'ds:1', hash: '2', data:" in text:
                console.print("Found AF_initDataCallback")
                text = text.lstrip(
                    "AF_initDataCallback({key: 'ds:1', hash: '2', data:"
                ).rstrip(", sideChannel: {}});")
                AF_initDataCallback = json.loads(text)
                results = self._parse_AF_initDataCallback(AF_initDataCallback, info)
                batch = Batch(results, self.session)
            elif text.startswith("var AF_initDataKeys"):
                console.print("Found AF_initDataKeys")
                info.rpcids = re.findall(r"'ds:1' : {id:'(.*)',", text)[0]
            elif text.startswith("window.WIZ_global_data"):
                console.print("Found window.WIZ_global_data")
                WIZ_global_data = json.loads(
                    re.findall(r"window.WIZ_global_data = (.*);", text)[0]
                )
                info.f_sid = WIZ_global_data["FdrFJe"]
                info.bl = WIZ_global_data["cfb2h"]

        return batch

    def _parse_response(self, content: str, info: SearchInfo) -> Batch:
        AF_initDataCallback = json.loads(
            re.findall(r'"HoAMBc","(.*)",null,null,null,"generic"]]\n', content)[0]
            .replace('\\"', '"')
            .replace('\\\\"', '\\"')
        )
        results = self._parse_AF_initDataCallback(AF_initDataCallback, info)
        batch = Batch(results, self.session)

        info.batchexecute_params["_reqid"] = (
            info.batchexecute_params["_reqid"] % 100000
        ) + (100000 * info.page_num)
        return batch

    def _form_async_query(self, info: SearchInfo):
        _pms = re.search(
            "/k=([^/]+)",
            info.xjs["basecomb"],
        )
        if not _pms:
            _pms = "s"
        else:
            _pms = _pms.group(1)
        params = {
            "arc_id": "srp_q_110",
            "ffilt": "all",
            "ve_name": "MoreResultsContainer",
            "use_ac": "false",
            "inf": "1",
            "_id": "",
            "_pms": _pms,
            "_fmt": "pc",
            "_basecss": quote_plus(info.xjs["basecss"]),
            "_basejs": quote_plus(info.xjs["basejs"]),
            "_basecomb": quote_plus(info.xjs["basecomb"]),
        }

    async def _get_params(self, search_info: SearchInfo):
        pass

    async def _make_request(
        self, method: str, url: str, params=None
    ) -> aiohttp.ClientResponse:
        if not self.session:
            self.session = aiohttp.ClientSession()
        response = await self.session.request(
            method,
            url,
            headers=self.headers,
            params=params,
        )
        return response


if __name__ == "__main__":

    async def main():
        try:
            google = ImageDownloader()
            async for batch in google.search("Hello world"):
                print(batch)
        except Exception:
            console.print_exception(show_locals=False)
        finally:
            if google.session:
                await google.session.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
