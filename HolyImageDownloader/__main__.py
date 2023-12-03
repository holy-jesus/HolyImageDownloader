import asyncio
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .google import ImageDownloader
from .result import Result
from .downloader import Downloader

app = typer.Typer()
console = Console()


@app.command()
def download(
    query: Annotated[str, typer.Argument(help="Your search query")] = None,
    path: Annotated[
        Optional[Path],
        typer.Option(
            "--path", "-p", help="Path where to save downloaded images", writable=True
        ),
    ] = "./images/",
    limit: Annotated[int, typer.Option(help="Number of images to download")] = -1,
    downloaders: Annotated[int, typer.Option(help="Number of concurrent downloads")] = 50,
    # maintain_aspect_ration: Annotated[bool, typer.Option(help="Maintain same aspect ratio as original image")] = False,
):
    if path.is_file():
        console.print("[red]ERROR. path is file.[/red]")
        return
    elif tuple(path.glob("*")):
        console.print("[yellow]WARNING. path is not empty[/yellow]")
    if downloaders > limit and limit != -1:
        downloaders = limit
    while not query:
        query = typer.prompt("Search query")
    path = path.joinpath(query.replace(" ", "_").lower() + "/")
    path.mkdir(parents=True, exist_ok=True)
    async def run():
        loop = asyncio.get_event_loop()
        google = ImageDownloader()
        results: list[Result] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Fetching images...", total=None)
            async for batch in google.search(query):
                results += batch.results
                progress.update(task, description=f"Fetching images... {len(results)} fetched.")
                if limit != -1 and len(results) > limit:
                    break
        results = results[:limit] if len(results) > limit else results
        downloader = Downloader(results, path, google.session, downloaders, maintain_aspect_ratio=False)
        downloader_task = loop.create_task(downloader.download())
        with Progress() as progress:
            task = progress.add_task("[green]Downloading...", total=len(results))
            while not downloader_task.done():
                await asyncio.sleep(0.25)
                progress.update(task, completed=downloader.downloaded)
        await google.session.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(lambda *args: print(arg for arg in args))
    loop.run_until_complete(run())


if __name__ == "__main__":
    app()
