from aiohttp import ClientSession

try:
    from result import Result
except ModuleNotFoundError:
    from .result import Result

class Batch:
    def __init__(self, results: dict, session: ClientSession) -> None:
        self.results: tuple[Result] = tuple(
            Result(result) for result in results
        )
        self.session = session

    def __len__(self):
        return len(self.results)

    def to_dict(self):
        return {"data": [result.to_dict() for result in self.results]}
