from dataclasses import dataclass

from HolyImageDownloader.ENUMS import (
    SafeSearch,
    Size,
    AspectRatio,
    Color,
    Type,
    UsageRights,
    FileType,
    Region,
)


@dataclass
class SearchInfo:
    search_query: str = None

    this_exact_word_or_phrase: str = None
    any_of_these_words: str = None
    none_of_these_words: str = None

    safe_search: SafeSearch = SafeSearch.FILTER

    image_size: Size = Size.ANY
    aspect_ratio: AspectRatio = AspectRatio.ANY
    colours_in_the_image: Color = Color.ANY
    type_of_image: Type = Type.ANY
    region: Region = Region.ANY
    site_or_domain: str = None
    file_type: FileType = FileType.ANY
    usage_rights: UsageRights = UsageRights.ANY

    arc_srp: str = None
    vet: str = None
    ved: str = None

    kEI: str = None
    kBL: str = None
    kOPI: str = None
    sca_esv: str = None
    as_st: str = "y"
    udm: str = None
    xjs: dict = None
    sn: str = "images"

    page_num: int = 0
