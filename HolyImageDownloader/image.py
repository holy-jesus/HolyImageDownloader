class Image:
    def __init__(self, json: list) -> None:
        self.url: str = json["url"]
        self.preview: bool = json["preview"]
        self.blurred: bool = json["blurred"]
        self.width: int = json["width"]
        self.height: int = json["height"]
        self.size: tuple[int, int] = (json["width"], json["height"])

    def __repr__(self) -> str:
        return f"Image(url={self.url}, size={self.width}x{self.height}, preview={self.preview}, blurred={self.blurred})"

    def to_dict(self):
        return {"url": self.url, "size": self.size}
