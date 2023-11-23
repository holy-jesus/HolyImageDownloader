from dataclasses import dataclass


@dataclass
class SearchInfo:
    search_query: str = None
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
