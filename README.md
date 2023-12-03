# HolyImageDownloader

> [Русский](https://github.com/holy-jesus/HolyImageDownloader/blob/main/README_ru.md)

This module is in an early stage of development, hence there's a lot of unimplemented functionality, broken features, and inadequate documentation, etc. Additionally, with each commit, everything can significantly change, break, etc.

## Key Features
- This module doesn't utilize Selenium, only direct requests to Google's browser API, reducing computer load and significantly decreasing image download time.

## Installation

```bash
pip install git+https://github.com/holy-jesus/HolyImageDownloader
```

## Usage

```bash
ImageDownloader "Your search query" --path ./path/ --limit 30 --downloaders 100
```

If the above command didn't work:

```bash
python -m HolyImageDownloader "Your search query" --path ./path/ --limit 30 --downloaders 100
```

`--path` - Optional, specifies the folder where the program will download all images. Default: ./images/your_search_query/

`--limit` - Optional, denotes the number of images to download. Use -1 to download all images. Default: -1

`--downloaders` - Optional, number of parallel image downloaders. Higher values speed up the process; excessively large numbers might have adverse effects. Default: 50

You can also run the command without specifying a search query; the program will prompt you for it:

```bash
$ ImageDownloader
Search query: 
# or
$ python -m HolyImageDownloader
Search query: 
```

It is still not possible to specify image sizes, required image size, and search filters on the command line.

### If you want to use the module in your program:

```python
import asyncio
from HolyImageDownloader import ImageDownloader

async def main():
    google = ImageDownloader()
    # Downloads all images. Arguments can specify filters, image sizes, and the number of downloaders.
    await google.download("Your search query")

    # Allows data parsing. Can be used for more flexible image downloads.
    async for batch in google.search("Your search query"):
        ...

asyncio.run(main())
```

## Use at your own risk

This software might, in theory, lead to your suspension or termination of access to Google services. Although I highly doubt it, you're solely responsible for using this software.

Here's an excerpt from Google's Terms of Service:

<blockquote>
<h3>Suspending or terminating your access to Google services</h1>

Google reserves the right to suspend or terminate your access to the services or delete your Google Account if any of these things happen:

- you materially or repeatedly breach these terms, service-specific additional terms or policies
- we’re required to do so to comply with a legal requirement or a court order
- we reasonably believe that your conduct causes harm or liability to a user, third party or Google – for example, by hacking, phishing, harassing, spamming, misleading others or scraping content that doesn’t belong to you
</blockquote>

You can read the full [Terms of Service from Google via this link](https://policies.google.com/terms).

###### Translated using ChatGPT