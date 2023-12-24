try:
    from image import Image
    from website import Website
except ModuleNotFoundError:
    from .image import Image
    from .website import Website

class Result:
    def __init__(self, json: list) -> None:
        self.website = Website(json["website"])
        self.image = Image(json["image"])
        self.preview = Image(json["preview"])
        self.blurred_preview: Image | None = Image(json["blurred"]) if json["blurred"] else None
        self.nsfw = bool(self.blurred_preview)

    def to_dict(self):
        return {"image": self.image.to_dict(), "preview": self.preview.to_dict(), "website": self.website.to_dict()}

    def __repr__(self) -> str:
        return f"Result(website={self.website}, preview={self.preview}, image={self.image})"
