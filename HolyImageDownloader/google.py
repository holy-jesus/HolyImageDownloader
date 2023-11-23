import asyncio
import os
import re
from datetime import datetime
from random import choice, randint
from typing import AsyncGenerator, Tuple
from urllib.parse import quote_plus
import codecs

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
import json

from searchinfo import SearchInfo
from batch import Batch
from ENUMS import Color, Size, Time, Type, UsageRights


class ImageDownloader:
    GOOGLE_IMAGES_BASE_URL = "https://www.google.com/imghp"
    GOOGLE_IMAGE_SEARCH_URL = "https://www.google.com/search"
    GOOGLE_BATCHEXECUTE_URL = (
        "https://www.google.com/_/VisualFrontendUi/data/batchexecute"
    )

    def __init__(self) -> None:
        self.session: aiohttp.ClientSession = None
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        }

    def __del__(self):
        pass
        # asyncio.get_event_loop().create_task(self.session.close())

    def search(
        self,
        search_query: str,
        size: Size = None,
        color: Color = None,
        type: Type = None,
        time: Time = None,
        usage_rights: UsageRights = None,
    ) -> AsyncGenerator[Batch, None]:
        if not search_query:
            raise ValueError("")
        elif not isinstance(search_query, str):
            raise ValueError("")

        quoted_search_query = quote_plus(search_query)
        params = {"q": quoted_search_query, "oq": quoted_search_query}
        tbs = ",".join(q.value for q in (size, color, type, time, usage_rights) if q)
        search_info = SearchInfo(search_query, tbs, params)
        return self._generator(search_info)

    async def _generator(
        self, search_info: SearchInfo
    ) -> AsyncGenerator[Batch, None]:
        await self._get_params(search_info)
        # tbs = search_params.get("tbs", None)
        response = await self._make_request(
            "GET", self.GOOGLE_IMAGE_SEARCH_URL, params=search_info.params
        )
        content = await response.content.read()
        batch = self._parse_page(
            content, search_info
        )
        yield batch
        while search_info.batchexecute_post is not None:
            response = await self.session.post(
                self.GOOGLE_BATCHEXECUTE_URL,
                data=search_info.batchexecute_post,
                params=search_info.batchexecute_params,
                headers=self.headers,
            )
            content = await response.text()
            batch = self._parse_batchexecute(
                content, search_info
            )
            yield batch


    async def download(
        self,
        search_query: str,
        size: Size = None,
        color: Color = None,
        type: Type = None,
        time: Time = None,
        usage_rights: UsageRights = None,
        number_of_downloaders: int = None,
        new_size: Tuple[int, int] = None,
    ):
        i = 1
        tasks = []
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        path = os.getcwd() + "/images/"
        if not os.path.isdir(path):
            os.mkdir(path)
        path += search_query + "/"
        if not os.path.isdir(path):
            os.mkdir(path)
        if not number_of_downloaders:
            number_of_downloaders = 10
        elif number_of_downloaders < 0:
            number_of_downloaders = 10
        for _ in range(number_of_downloaders):
            tasks.append(loop.create_task(self._downloader(queue, path, new_size)))
        async for batch in self.search(
            search_query, size, color, type, time, usage_rights
        ):
            for result in batch.results:
                await queue.put((result.image, str(i)))
                i += 1
        await queue.join()
        for task in tasks:
            task.cancel()

    async def _downloader(
        self,
        queue: asyncio.Queue,
        path_to_save: str,
        new_size: Tuple[int, int] = None,
    ):
        while True:
            image, filename = await queue.get()
            content, format = await image.download(new_size)
            if content is None:
                queue.task_done()
                continue
            async with aiofiles.open(
                f"{path_to_save}/{filename}.{format}", "wb"
            ) as file:
                await file.write(content)
            queue.task_done()

    def _parse_AF_initDataCallback(self, AF_initDataCallback: dict, info: SearchInfo):
        if len(AF_initDataCallback[56]) < 2:
            # По этому поисковому запросу нету картинок
            info.grid_state = None
            info.cursor = None
            info.batchexecute_post = None

            return None
        elif not AF_initDataCallback[56][1][0][0][0][0]["444383007"][12][16]:
            # Картинки законичились
            info.grid_state = None
            info.cursor = None
            info.batchexecute_post = None
        else:
            batchexecute_data = AF_initDataCallback[56][1][0][0][0][0]["444383007"][12]
            info.grid_state = batchexecute_data[11]
            info.cursor = (
                codecs.decode(batchexecute_data[16][3], 'unicode_escape'),
                codecs.decode(batchexecute_data[16][4], 'unicode_escape'),
            )

        results = []
        for result in AF_initDataCallback[56][1][0][0][1][0]:
            if result[0][0]["444383007"][1] is None:
                continue
            result = result[0][0]["444383007"][1]
            preview = {
                "url": result[2][0],
                "width": int(result[2][2]),
                "height": int(result[2][1]),
            }
            image = {
                "url": result[3][0],
                "width": int(result[3][2]),
                "height": int(result[3][1]),
            }
            website = {
                "url": result[25]["2003"][2],
                "base_url": result[25]["2003"][17],
                "title": result[25]["2003"][3],
                "name": result[25]["2003"][12],
            }
            results.append({"preview": preview, "image": image, "website": website})
        return results

    def _parse_page(
        self, content: str, info: SearchInfo
    ) -> Batch:
        batch = None
        soup = BeautifulSoup(content, "lxml")
        for script in soup.select("script"):
            text = script.get_text()
            if "AF_initDataCallback({key: 'ds:1', hash: '2', data:" in text:
                text = text.lstrip(
                    "AF_initDataCallback({key: 'ds:1', hash: '2', data:"
                ).rstrip(", sideChannel: {}});")
                AF_initDataCallback = json.loads(text)
                results = self._parse_AF_initDataCallback(AF_initDataCallback, info)
                batch = Batch(results, self.session)
            elif text.startswith("var AF_initDataKeys"):
                info.rpcids = re.findall(r"'ds:1' : {id:'(.*)',", text)[0]
            elif text.startswith("window.WIZ_global_data"):
                WIZ_global_data = json.loads(re.findall(r"window.WIZ_global_data = (.*);", text)[0])
                info.f_sid = WIZ_global_data["FdrFJe"]
                info.bl = WIZ_global_data["cfb2h"]
        self._generate_batchexecute_post(info)
        self._generate_batchexecute_params(info)
        return batch

    def _parse_batchexecute(
        self, content: str, info: SearchInfo
    ) -> Batch:
        AF_initDataCallback = json.loads(re.findall(r'"HoAMBc","(.*)",null,null,null,"generic"]]\n', content)[0].replace("\\\"", "\"").replace("\\\\\"", "\\\""))
        results = self._parse_AF_initDataCallback(AF_initDataCallback, info)
        batch = Batch(results, self.session)
        self._generate_batchexecute_post(info)
        info.batchexecute_params["_reqid"] = (
            info.batchexecute_params["_reqid"] % 100000
        ) + (100000 * info.page_num)
        return batch

    def _generate_batchexecute_post(self, info: SearchInfo) -> None:
        if info.cursor is None:
            info.batchexecute_post = None
            return 
        data = (
            [None, None, info.grid_state]
            + 25 * [None]
            + [[info.search_query, "en"] + 18 * [None] + [info.tbs] + 9 * [None] + [[]]]
            + 8 * [None]
            + [[None, info.cursor[0], info.cursor[1]]]
            + [None, False]
        )
        f_req = json.dumps(
            [
                [
                    [
                        info.rpcids,
                        json.dumps(data),
                        None,
                        "generic",
                    ]
                ]
            ]
        )
        info.batchexecute_post = {"f.req": f_req + "&"}
        info.page_num = info.grid_state[0]

    def _generate_batchexecute_params(self, info: SearchInfo) -> dict:
        now = datetime.now()
        info.batchexecute_params = {
            "source-path": "/search",
            "hl": "en-US", # Получать язык пользователя?
            "authuser": "",
            "soc-app": "162",
            "soc-platform": "1",
            "soc-device": "1",
            "_reqid": 1
            + (3600 * now.hour + 60 * now.minute + now.second)
            + (100000 * 1),
            "rt": "c",
            "f.sid": info.f_sid,
            "bl": info.bl,
        }

    async def _get_params(self, search_info: SearchInfo):
        response = await self._make_request("GET", self.GOOGLE_IMAGES_BASE_URL)
        content = await response.content.read()
        w, h = choice(
            (
                (3840, 2160),
                (2560, 1440),
                (1920, 1080),
                (1366, 768),
                (1280, 720),
                (1024, 576),
            )
        )
        search_info.params.update({
            "biw": randint(int(w * 0.75), w),
            "bih": randint(int(h * 0.75), h),
        })
        soup = BeautifulSoup(content, "lxml")
        div = soup.find("div", {"id": "tophf"})
        inputs = div.find_all("input")
        for input in inputs:
            if not input.get("value", None):
                continue
            value = input["value"]
            search_info.params[input["name"]] = value

    async def _make_request(
        self, method: str, url: str, params=None
    ) -> aiohttp.ClientResponse:
        if not self.session:
            self.session = aiohttp.ClientSession()
        response = await self.session.request(
            method, url, headers=self.headers, params=params
        )
        return response


if __name__ == "__main__":

    async def main():
        downloader = ImageDownloader()
        async for query in downloader.search("Hello world"):
            print(query.to_dict()["data"][0])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
# f.req=[[["HoAMBc","[null,null,[1,null,199,1,1920,[],[],[],null,null,null,166],null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[\"hello world\",\"ru\",null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,\"hp\",null,null,null,null,null,null,null,null,[]],null,null,null,null,null,null,null,null,[null,\"CAE=\",\"GGggAA==\"]]",null,"generic"]]]&