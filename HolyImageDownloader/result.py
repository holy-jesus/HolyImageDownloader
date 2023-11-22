from image import Image
from website import Website


class Result:
    def __init__(self, json: list, session) -> None:
        self.website = Website(json["website"])
        self.preview = Image(json["preview"], session)
        self.image = Image(json["image"], session)

    def to_dict(self):
        return {"image": self.image.to_dict(), "preview": self.preview.to_dict(), "website": self.website.to_dict()}

    def __repr__(self) -> str:
        return f"Result(website={self.website}, preview={self.preview}, image={self.image})"
