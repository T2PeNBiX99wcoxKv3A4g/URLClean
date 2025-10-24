import time
from urllib.parse import urlparse

import pyperclip
import requests
import typer
from icecream import ic

app = typer.Typer()
redirection_status_codes = [301, 302, 307, 308]


class NoneUrlException(Exception):
    pass


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
        raise NoneUrlException("URL is None")
    try:
        response = ic(requests.head(url))
        if ic(response.status_code) in redirection_status_codes:
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
def fetch_true_url(url: str, only_fetch: bool = False, debug: bool = False):
    debug_output_control(debug)
    actual_url = get_actual_url(url)
    if actual_url is None:
        typer.echo(f"Error: Unable to get actual URL of {url}")
        typer.Exit(code=1)
        return
    return_url = actual_url if only_fetch else get_clean_url(actual_url)
    pyperclip.copy(return_url)
    typer.echo(f"Cleaned URL: {return_url}")
    typer.echo(f"Copied to clipboard")


@app.command()
def clipboard_watchers(only_fetch: bool = False, sleep_seconds: float = 1, debug: bool = False):
    debug_output_control(debug)

    last_clipboard_content = None

    while True:
        try:
            clipboard_content = pyperclip.paste()

            if type(clipboard_content) != str:
                continue

            if clipboard_content == last_clipboard_content:
                continue

            last_clipboard_content = ic(clipboard_content)

            # noinspection HttpUrlsUsage
            if ic(not clipboard_content.startswith("http://")) and ic(not clipboard_content.startswith("https://")):
                continue

            typer.echo(f"Found URL in clipboard: {clipboard_content}")

            actual_url = get_actual_url(clipboard_content)

            if actual_url is None:
                typer.echo(f"Error: Unable to get actual URL or {clipboard_content}")
                continue

            return_url = actual_url if only_fetch else get_clean_url(actual_url)
            last_clipboard_content = return_url
            pyperclip.copy(return_url)
            typer.echo(f"Cleaned URL: {return_url}")
            typer.echo(f"Copied to clipboard")
        except Exception as e:
            typer.echo(f"Error: {e}")
        finally:
            time.sleep(sleep_seconds)


if __name__ == '__main__':
    app()
