# HolyImageDownloader

> [Russian](https://github.com/holy-jesus/HolyImageDownloader/blob/main/README_ru.md)

This module is in the early stages of development, so there is a lot of functionality that is not implemented, broken functionality, poor documentation, etc. Also, with each commit, everything can significantly change, break, etc.

## Key Features
- This module does not use Selenium, only direct requests to Google's internal API, reducing the load on the computer and significantly reducing the time it takes to download images.

## Installation


```bash
pip install git+https://github.com/holy-jesus/HolyImageDownloader
```

## Usage

```bash
ImageDownloader "Your search query"
```

If the above command didn't work:

```bash
python -m HolyImageDownloader "Your search query"
```

At the moment, when using the program in CLI mode, it downloads all images, and specifying the number of images (for now) is not possible. It is also not possible to specify the required image format, image size, and search filters.

If you want to use it in Python:
```python
import asyncio
from HolyImageDownloader import ImageDownloader

async def main():
    google = ImageDownloader()
    # Downloads all images. You can specify filters, image size, and the number of downloaders in the arguments.
    await google.download("Your search query")

    # Allows parsing data. It can also be used for more flexible image downloads.
    async for batch in google.search("Your search query"):
        ...

asyncio.run(main())
```

