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


def get_actual_url(url: str) -> str:
    response = requests.head(url)
    headers = ic(response.headers)
    if "location" in headers:
        return get_actual_url(headers["location"])
    return url


@app.command()
def clean_url(url: str, debug: bool = False):
    debug_output_control(debug)
    actual_url = get_actual_url(url)
    url_parse = ic(urlparse(actual_url))
    get_clean_url = ic(url_parse.scheme + "://" + url_parse.netloc + url_parse.path)
    pyperclip.copy(get_clean_url)
    typer.echo(f"Cleaned URL: {get_clean_url}")
    typer.echo(f"Copied to clipboard")


if __name__ == '__main__':
    app()
