from dataclasses import dataclass

try:
    from ENUMS import SafeSearch
except ImportError:
    from .ENUMS import SafeSearch


@dataclass
class SearchInfo:
    search_query: str = None
    safe_search: SafeSearch = SafeSearch.FILTER
    tbs: str = None
    params: dict = None
    rpcids: str = None
    f_sid: str = None
    bl: str = None
    grid_state: list | None = None
    cursor: tuple | None = None
    batchexecute_params: dict | None = None
    batchexecute_post: dict | None = None
    page_num: int = 1
