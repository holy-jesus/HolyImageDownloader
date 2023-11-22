import typer

# https://typer.tiangolo.com/


app = typer.Typer()

@app.command()
def download():
    pass

if __name__ == "__main__":
    app()
