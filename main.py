from urllib.parse import urlparse

import pyperclip
import requests
import typer
from icecream import ic

app = typer.Typer()


def debug_output_control(debug: bool) -> None:
    if debug:
        ic.enable()
    else:
        ic.disable()


def get_clean_url(url: str) -> str:
    url_parse = ic(urlparse(url))
    return ic(url_parse.scheme + "://" + url_parse.netloc + url_parse.path)


def get_actual_url(url: str) -> str | None:
    if url is None:
        raise Exception("URL is None")
    try:
        response = ic(requests.head(url))
        if ic(response.status_code) == 302:
            headers = ic(response.headers)
            return get_actual_url(ic(headers["location"]))
        return url
    except Exception as e:
        typer.echo(f"Error: {e}")
        return None


@app.command()
def clean_url(url: str, debug: bool = False):
    debug_output_control(debug)
    the_clean_url = get_clean_url(url)
    pyperclip.copy(the_clean_url)
    typer.echo(f"Cleaned URL: {the_clean_url}")
    typer.echo(f"Copied to clipboard")


@app.command()
def fetch_true_url(url: str, debug: bool = False):
    debug_output_control(debug)
    actual_url = get_actual_url(url)
    if actual_url is None:
        typer.echo("Error: Unable to get actual URL")
        typer.Exit(code=1)
        return
    the_clean_url = get_clean_url(actual_url)
    pyperclip.copy(the_clean_url)
    typer.echo(f"Cleaned URL: {the_clean_url}")
    typer.echo(f"Copied to clipboard")


if __name__ == '__main__':
    app()
