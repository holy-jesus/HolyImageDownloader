import asyncio
import typer
from rich.console import Console

from .google import ImageDownloader

app = typer.Typer()
console = Console()

@app.command()
def download(query: str = None):
    while not query:
        query = typer.prompt("Search query")

    async def run():
        downloader = ImageDownloader()
        await downloader.download(query)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())

if __name__ == "__main__":
    app()
