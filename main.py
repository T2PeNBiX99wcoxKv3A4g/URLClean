import json
import os
import time

import pyperclip
import requests
import typer
from icecream import ic
from yarl import URL

from sha256check import hash_file_check

app = typer.Typer()
redirection_status_codes = [301, 302, 307, 308]


class NoneUrlException(Exception):
    pass


class DownloadException(Exception):
    pass


def debug_output_control(debug: bool) -> None:
    if debug:
        ic.enable()
    else:
        ic.disable()


whitelist = {}
whitelist_path = "./whitelist.json"
whitelist_hash_path = whitelist_path + ".sha256"
whitelist_last_downloaded_path = whitelist_path + ".last_downloaded"
whitelist_hash_last_downloaded_path = whitelist_hash_path + ".last_downloaded"
whitelist_download_interval = 3600


def is_skip_download(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    with open(path, "r") as file:
        try:
            last_downloaded = float(file.read())
            return time.time() - last_downloaded < whitelist_download_interval
        except ValueError:
            return False


def create_last_downloaded_file(path: str) -> None:
    time_now = ic(time.time())
    with open(path, "w") as file:
        file.write(str(time_now))


def download_white_list(force: bool = False) -> bool:
    if not force and is_skip_download(whitelist_last_downloaded_path) and os.path.isfile(whitelist_path):
        return True
    file_response = ic(requests.get(
        "https://raw.githubusercontent.com/T2PeNBiX99wcoxKv3A4g/URLClean.Whitelist/refs/heads/master/whitelist.json"))
    if file_response.status_code != 200:
        return False
    with open(whitelist_path, "wb") as file:
        file.write(file_response.content)
    create_last_downloaded_file(whitelist_last_downloaded_path)
    return True


def download_white_list_hash(force: bool = False) -> bool:
    if not force and is_skip_download(whitelist_hash_last_downloaded_path) and os.path.isfile(whitelist_hash_path):
        return True
    file_response = ic(requests.get(
        "https://raw.githubusercontent.com/T2PeNBiX99wcoxKv3A4g/URLClean.Whitelist/refs/heads/master/whitelist.json.sha256"))
    if file_response.status_code != 200:
        return False
    with open(whitelist_hash_path, "wb") as file:
        file.write(file_response.content)
    create_last_downloaded_file(whitelist_hash_last_downloaded_path)
    return True


def upgrade_white_list_or_do_nothing() -> None:
    if not os.path.isfile(whitelist_path):
        if not download_white_list():
            raise DownloadException("Unable to download whitelist")
        return
    if not download_white_list_hash() and not os.path.isfile(whitelist_hash_path):
        raise DownloadException("Unable to download whitelist hash")
    if not hash_file_check(whitelist_hash_path):
        download_white_list()


def get_whitelist() -> None:
    global whitelist
    upgrade_white_list_or_do_nothing()
    with open(whitelist_path, "r") as file:
        get_list = {}
        try:
            get_list = ic(json.loads(file.read()))
        except json.decoder.JSONDecodeError as e:
            typer.echo(f"Error: Invalid whitelist file\n{e}")
        if len(get_list) < 1:
            return
        whitelist = get_list


def get_clean_url(url: str) -> str:
    get_whitelist()
    parsed_url = ic(URL(url))
    host = ic(parsed_url.host)
    path = ic(parsed_url.raw_path)
    allow_query_paths = whitelist[host] if host in whitelist else []
    allow_query_params = allow_query_paths[path] if path in allow_query_paths else []
    new_query_params = {}
    for param in ic(parsed_url.query.items()):
        if ic(param[0]) not in allow_query_params:
            continue
        new_query_params[param[0]] = param[1]
    return ic(parsed_url.with_query(new_query_params).human_repr())


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
def whitelist_update(debug: bool = False) -> None:
    debug_output_control(debug)
    download_white_list(True)
    download_white_list_hash(True)
    typer.echo("Force whitelist updated")


@app.command()
def clean_url(url: str, download_interval: int = 3600, debug: bool = False):
    global whitelist_download_interval
    debug_output_control(debug)
    whitelist_download_interval = download_interval
    the_clean_url = get_clean_url(url)
    pyperclip.copy(the_clean_url)
    typer.echo(f"Cleaned URL: {the_clean_url}")
    typer.echo(f"Copied to clipboard")


@app.command()
def fetch_true_url(url: str, only_fetch: bool = False, download_interval: int = 3600, debug: bool = False):
    global whitelist_download_interval
    debug_output_control(debug)
    whitelist_download_interval = download_interval
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
def clipboard_watchers(only_fetch: bool = False, sleep_seconds: float = 1, download_interval: int = 3600,
                       debug: bool = False):
    global whitelist_download_interval
    debug_output_control(debug)
    whitelist_download_interval = download_interval
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

            if return_url == last_clipboard_content:
                continue

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
