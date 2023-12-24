from enum import Enum


class Size(Enum):
    LARGE = "tsz:l"
    MEDIUM = "tsz:m"
    ICON = "tsz:i"


class Color(Enum):
    BLACK_AND_WHITE = "ic:gray"
    TRANSPARENT = "ic:trans"
    RED = "ic:specific,isc:red"
    ORANGE = "ic:specific,isc:orange"
    YELLOW = "ic:specific,isc:yellow"
    GREEN = "ic:specific,isc:green"
    TEAL = "ic:specific,isc:teal"
    BLUE = "ic:specific,isc:blue"
    PURPLE = "ic:specific,isc:purple"
    PINK = "ic:specific,isc:pink"
    WHITE = "ic:specific,isc:white"
    GRAY = "ic:specific,isc:gray"
    BLACK = "ic:specific,isc:black"
    BROWN = "ic:specific,isc:brown"


class Type(Enum):
    CLIP_ART = "itp:clipart"
    LINE_DRAWING = "itp:lineart"
    GIF = "itp:animated"


class Time(Enum):
    DAY = "qdr:d"
    WEEK = "qdr:w"
    MONTH = "qdr:m"
    YEAR = "qdr:y"


class UsageRights(Enum):
    CREATIVE_COMMONS_LICENSES = "il:cl"
    COMMERCIAL_AND_OTHER_LICENSES = "il:ol"


class SafeSearch(Enum):
    FILTER = "on"
    BLUR = "images"
    OFF = "off"