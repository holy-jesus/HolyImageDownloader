from dataclasses import dataclass


@dataclass
class SearchInfo:
    search_query: str = None
    tbs: str = None
    params: dict = None
    rpcids: str = None
    f_sid: str = None
    bl: str = None
    grid_state: list = None
    cursor: tuple = None
    batchexecute_params: dict = None
    batchexecute_post: dict = None
    page_num: int = 1
