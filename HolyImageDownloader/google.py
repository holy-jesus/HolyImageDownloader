import asyncio
import re
import json
from typing import AsyncGenerator, Tuple
from urllib.parse import quote_plus
from pathlib import Path

import js2py
import aiohttp
import json5
from bs4 import BeautifulSoup
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console

from HolyImageDownloader.searchinfo import SearchInfo
from HolyImageDownloader.batch import Batch
from HolyImageDownloader.ENUMS import (
    Color,
    Size,
    Time,
    Type,
    UsageRights,
    SafeSearch,
    AspectRatio,
    Region,
    FileType,
)
from HolyImageDownloader.config import HEADERS, URL
from HolyImageDownloader.downloader import Downloader
from HolyImageDownloader.utils import exclude_empty_values

console = Console()
_type = type
_SPECIFIC_COLORS = (
    Color.RED,
    Color.ORANGE,
    Color.YELLOW,
    Color.GREEN,
    Color.TEAL,
    Color.BLUE,
    Color.PURPLE,
    Color.PINK,
    Color.WHITE,
    Color.GRAY,
    Color.BLACK,
    Color.BROWN,
)


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
        *,
        this_exact_word_or_phrase: str = None,
        any_of_these_words: str = None,
        none_of_these_words: str = None,
        safe_search: SafeSearch = SafeSearch.FILTER,
        image_size: Size = Size.ANY,
        aspect_ratio: AspectRatio = AspectRatio.ANY,
        colours_in_the_image: Color = Color.ANY,
        type_of_image: Type = Type.ANY,
        region: Region = Region.ANY,
        site_or_domain: str = None,
        file_type: FileType = FileType.ANY,
        usage_rights: UsageRights = UsageRights.ANY,
    ) -> AsyncGenerator[Batch, None]:
        if not search_query:
            raise ValueError("Search query can't be empty.")
        elif not isinstance(search_query, str):
            raise ValueError(
                f'Search query must be type "str", not "{_type(search_query)}"'
            )
        info = SearchInfo(
            search_query=search_query,
            this_exact_word_or_phrase=this_exact_word_or_phrase,
            any_of_these_words=any_of_these_words,
            none_of_these_words=none_of_these_words,
            safe_search=safe_search,
            image_size=image_size,
            aspect_ratio=aspect_ratio,
            colours_in_the_image=colours_in_the_image,
            type_of_image=type_of_image,
            region=region,
            site_or_domain=site_or_domain,
            file_type=file_type,
            usage_rights=usage_rights,
        )
        return self._generator(info)

    async def download(
        self,
        search_query: str,
        path: Path | str | None = None,
        *,
        this_exact_word_or_phrase: str = None,
        any_of_these_words: str = None,
        none_of_these_words: str = None,
        safe_search: SafeSearch = SafeSearch.FILTER,
        image_size: Size = Size.ANY,
        aspect_ratio: AspectRatio = AspectRatio.ANY,
        colours_in_the_image: Color = Color.ANY,
        type_of_image: Type = Type.ANY,
        region: Region = Region.ANY,
        site_or_domain: str = None,
        file_type: FileType = FileType.ANY,
        usage_rights: UsageRights = UsageRights.ANY,

        max_images: int = None,
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
                search_query=search_query,
                this_exact_word_or_phrase=this_exact_word_or_phrase,
                any_of_these_words=any_of_these_words,
                none_of_these_words=none_of_these_words,
                safe_search=safe_search,
                image_size=image_size,
                aspect_ratio=aspect_ratio,
                colours_in_the_image=colours_in_the_image,
                type_of_image=type_of_image,
                region=region,
                site_or_domain=site_or_domain,
                file_type=file_type,
                usage_rights=usage_rights,
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

    async def _generator(self, info: SearchInfo) -> AsyncGenerator[Batch, None]:
        imgc, imgcolor = info.colours_in_the_image.value, ""
        if "specific:" in imgc:
            imgc, imgcolor = imgc.split(":")

        await self._switch_safe_search(info)
        console.print("Switched SafeSearch")

        response = await self._make_request(
            "GET",
            URL.SEARCH,
            exclude_empty_values(
                {
                    "as_st": "y",
                    "tbm": "isch",
                    "as_q": info.search_query,
                    "as_epq": info.this_exact_word_or_phrase,
                    "as_oq": info.any_of_these_words,
                    "as_eq": info.none_of_these_words,
                    "imgsz": info.image_size.value,
                    "imgar": info.aspect_ratio.value,
                    "imgc": imgc,
                    "imgcolor": imgcolor,
                    "imgtype": info.type_of_image.value,
                    "cr": info.region.value,
                    "as_sitesearch": info.site_or_domain,
                    "as_filetype": info.file_type.value,
                    "tbs": "",
                }
            ),
        )
        content = await response.text()
        with open("dump/page", "w") as f:
            f.write(content)
        batch, params = self._process_page(content, info)
        yield batch
        while info.vet is not None:
            response = await self._make_request("GET", URL.SEARCH, params)
            text = await response.text()
            with open(f"dump/response{info.page_num}", "w") as f:
                f.write(text)
            batch, params = self._process_response(text, info)
            yield batch
        return

    def _process_page(
        self, content: str, info: SearchInfo
    ) -> tuple[Batch | None, dict]:
        soup = BeautifulSoup(content, "lxml")
        batch = self._parse_page(content, soup, info)
        params = self._get_params(info)
        return batch, params

    def _process_response(
        self, content: str, info: SearchInfo
    ) -> tuple[Batch | None, dict]:
        batch = self._parse_response(content, info)
        params = self._get_params(info) if info.vet else None
        return batch, params

    def _parse_page(
        self, content: str, soup: BeautifulSoup, info: SearchInfo
    ) -> Batch | None:
        function_pattern = r"\(function\s*\(\)\s*\{([\s\S]*?)\}\s*\)\(\);"
        match = re.search(
            r"\{basecomb:'[^']+',basecss:'[^']+',basejs:'[^']+',excm:\[[^\]]+\]\}",
            content,
        )
        if not match:
            raise Exception("")  # TODO
        xjs = json5.loads(match.group())
        info.xjs = xjs

        inputs = soup.find(attrs={"id": "tophf"})
        info.sca_esv = inputs.find("input", {"name": "sca_esv"})["value"]
        info.as_st = inputs.find("input", {"name": "as_st"})["value"]
        info.udm = inputs.find("input", {"name": "udm"})["value"]

        next = soup.find(attrs={"jsname": "sgxt2d"})
        prev = soup.find(attrs={"jsname": "EvDH1d"})

        assert next
        assert prev

        arc_srp = next["id"]
        vet = next["data-ved"]
        ved = prev["data-ved"]

        info.arc_srp = arc_srp
        info.vet = vet
        info.ved = ved

        batch = None

        for script in soup.select("script"):
            text = script.get_text()
            if "{kEI:" in text:
                function_text = re.findall(function_pattern, text)[0]
                match = re.search(r"var\s+_g\s*=\s*\{[^}]+\}", function_text)
                _g = js2py.eval_js(match.group(0))
                info.kBL = _g["kBL"]
                info.kEI = _g["kEI"]
                info.kOPI = str(_g["kOPI"])
            if "google.sn=" in text:
                function_text = re.findall(function_pattern, text)[1]
                matches = re.findall(r"google\.(\w+)='(.*?)';", function_text)
                result = {key: value for key, value in matches}
                info.sn = _g[result["sn"]]
            if "window.WIZ_global_data" in text:
                initial_data = re.findall(function_pattern, text)[6].split(
                    ";var a=m;", 1
                )[0]
                data = js2py.eval_js(initial_data).to_dict()
                batch = self._parse_images(data.values())
        return batch

    def _parse_images(self, objects: list) -> Batch | None:
        results = []
        for value in objects:
            if len(value) < 2 or value[0] != 1 or not isinstance(value[1], list):
                continue

            if len(value) >= 26:

                preview = {
                    "url": value[1][20][0],
                    "height": value[1][20][1],
                    "width": value[1][20][2],
                    "preview": True,
                    "blurred": False,
                }
                blurred = {
                    "url": value[1][2][0],
                    "height": value[1][2][1],
                    "width": value[1][2][2],
                    "preview": True,
                    "blurred": True,
                }
            else:
                preview = {
                    "url": value[1][2][0],
                    "height": value[1][2][1],
                    "width": value[1][2][2],
                    "preview": True,
                    "blurred": False,
                }
                blurred = None
            image = {
                "url": value[1][3][0],
                "height": value[1][3][1],
                "width": value[1][3][2],
                "preview": False,
                "blurred": False,
            }

            if isinstance(value[1][9], dict):
                info = value[1][9]
            else:
                info = value[1][-1]
            website = {
                "url": info["2003"][2],
                "base_url": info["2003"][17],
                "title": info["2003"][3],
                "name": info["2003"][12],
            }
            results.append(
                {
                    "preview": preview,
                    "image": image,
                    "website": website,
                    "blurred": blurred,
                }
            )
        if not results:
            return None
        batch = Batch(results, self.session)
        return batch

    def _parse_response(self, content: str, info: SearchInfo) -> Batch:
        content = content.lstrip(")]}'\n")
        parts = []
        vet = None
        while True:
            try:
                index = content.index(";")
            except ValueError:
                break
            result = bool(re.match(r"^[0-9A-Fa-f]+", content[:index]))
            if not result:
                content = content[index + 1 :]
                continue
            length = int(content[:index], 16)
            part = content[index + 1 : length + index + 1]
            content = content[length + index + 1 :]
            if not part:
                continue
            parts.append(part)
            if "arc-npt" in part:
                soup = BeautifulSoup(part, "lxml")
                arc = soup.find(attrs={"class": "arc-npt"})
                vet = arc["data-ved"]
        info.vet = vet
        data = json.loads(parts[-1])
        objects = []
        for obj in data[0]:
            try:
                objects.append(json.loads(obj[1]))
            except json.JSONDecodeError:
                continue
        batch = self._parse_images(objects)

        return batch

    def _form_async_query(self, _id: str, info: SearchInfo):
        _pms = re.search(
            "/k=([^/]+)",
            info.xjs["basecomb"],
        )
        if not _pms:
            _pms = "s"
        else:
            _pms = _pms.group(1).split(".")[1]
        params = {
            "arc_id": _id.lstrip("arc-") + str(info.page_num * 10),
            "ffilt": "all",
            "ve_name": "MoreResultsContainer",
            "use_ac": "false",
            "inf": "1",
            "_id": _id + str(info.page_num * 10),
            "_pms": _pms,
            "_fmt": "pc",
            "_basejs": (info.xjs["basejs"]),
            "_basecss": (info.xjs["basecss"]),
            "_basecomb": (info.xjs["basecomb"]),
        }
        text = ",".join(f"{key}:{value}" for key, value in params.items())
        return text

    def _get_params(self, info: SearchInfo):
        async_query = self._form_async_query(info.arc_srp, info)

        info.page_num += 1

        params = {
            "vet": "1" + info.vet + "..i",
            "ved": info.ved,
            "bl": info.kBL,
            "s": info.sn or "images",
            "opi": info.kOPI,
            "udm": info.udm,
            # yv is always assigned the value 3.
            "yv": "3",
            "q": quote_plus(info.search_query),
            "sca_esv": info.sca_esv,
            "as_st": info.as_st or "y",
            "ei": info.kEI,
            "start": str(info.page_num * 10),
            "sa": "N",
            # asearch most likely indicates the reason for loading, and arc indicates that the reason is scrolling through the page.
            "asearch": "arc",
            "cs": "0",
            "async": async_query,
        }
        return params

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
            await google.download("Hello world", "./images/")
        except Exception:
            console.print_exception(show_locals=False)
        finally:
            if google.session:
                await google.session.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
