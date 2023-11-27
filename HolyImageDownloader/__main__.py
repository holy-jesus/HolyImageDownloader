import asyncio
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated

import typer
from rich.console import Console

from .google import ImageDownloader

app = typer.Typer()
console = Console()

@app.command()
def download(
    query: Annotated[str, typer.Argument(help="Your search query")] = None,
    path: Annotated[
        Optional[Path], typer.Option("--path", "-p", help="Path where to save downloaded images", writable=True)
    ] = "./images/",
    max_images: Annotated[int, typer.Option(help="Number of images to download")] = -1,
    downloaders: Annotated[int, typer.Option()] = 10
):
    if path.is_file():
        console.print("[red]path_to_save is file.[/red]")
        return
    elif tuple(path.glob("*")):
        console.print("[yellow]WARNING. path_to_save is not empty[/yellow]")
    while not query:
        query = typer.prompt("Search query")

    async def run():
        downloader = ImageDownloader()
        await downloader.download(query, max_images=max_images, number_of_downloaders=downloaders)
        await downloader.session.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())


if __name__ == "__main__":
    app()
