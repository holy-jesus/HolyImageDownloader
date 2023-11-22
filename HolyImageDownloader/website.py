from urllib.parse import unquote_plus


class Website:
    def __init__(self, json: list) -> None:
        self.url: str = unquote_plus(json["url"])
        self.base_url: str = unquote_plus(json["base_url"])
        self.title: str = unquote_plus(json["title"])
        self.name = unquote_plus(json["name"])

    def __repr__(self) -> str:
        return f"Website(title={self.title}, name={self.name}, url={self.url}, base_url={self.base_url}"

    def to_dict(self):
        return {"url": self.url, "base_url": self.base_url, "title": self.title, "name": self.name}
