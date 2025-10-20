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


def clean_url(url: str) -> str:
    url_parse = ic(urlparse(url))
    return ic(url_parse.scheme + "://" + url_parse.netloc + url_parse.path)


def get_actual_url(url: str) -> str:
    if url is None:
        raise Exception("URL is None")
    response = ic(requests.head(url))
    if ic(response.status_code) == 302:
        headers = ic(response.headers)
        return get_actual_url(ic(headers["location"]))
    return url


@app.command()
def get(url: str, debug: bool = False):
    debug_output_control(debug)
    actual_url = get_actual_url(url)
    pyperclip.copy(actual_url)
    typer.echo(f"Cleaned URL: {actual_url}")
    typer.echo(f"Copied to clipboard")


if __name__ == '__main__':
    app()
