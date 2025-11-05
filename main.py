import json
import os
import sys
import time

import pyperclip
import requests
import typer
from icecream import ic
from yarl import URL

from sha256check import hash_file_check

app = typer.Typer()
redirection_status_codes = [301, 302, 303, 307, 308]


def get_data_dir() -> str:
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)


global_download_interval = 3600
whitelist = {}
whitelist_file = "whitelist.json"
blacklist = {}
blacklist_file = "blacklist.json"


class NoneUrlException(Exception):
    pass


class DownloadException(Exception):
    pass


def debug_output_control(debug: bool) -> None:
    if debug:
        ic.enable()
    else:
        ic.disable()


def is_skip_download(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    with open(path, "r") as file:
        try:
            last_downloaded = float(file.read())
            return ic(time.time() - last_downloaded) < global_download_interval
        except ValueError:
            return False


def create_last_downloaded_file(path: str) -> None:
    time_now = ic(time.time())
    with open(path, "w") as file:
        file.write(str(time_now))


def download(url: str, path: str, force: bool = False) -> bool:
    last_downloaded_file = f"{path}.last_downloaded"
    if not force and ic(is_skip_download(last_downloaded_file)) and os.path.isfile(path):
        return True
    file_response = ic(requests.get(url))
    if file_response.status_code != 200:
        return False
    with open(path, "wb") as file:
        file.write(file_response.content)
    create_last_downloaded_file(last_downloaded_file)
    return True


def download_file(filename: str, force: bool = False) -> bool:
    return download(
        f"https://raw.githubusercontent.com/T2PeNBiX99wcoxKv3A4g/URLClean.Whitelist/refs/heads/master/{filename}",
        os.path.join(get_data_dir(), filename), force)


def upgrade_list_or_do_nothing(filename: str, force: bool = False) -> str:
    hash_file = f"{filename}.sha256"
    file_path = ic(os.path.join(get_data_dir(), filename))
    file_hash_path = ic(os.path.join(get_data_dir(), hash_file))
    if not os.path.isfile(file_path):
        if not download_file(filename, force):
            raise DownloadException(f"Unable to download {filename}")
        return file_path
    if not download_file(hash_file, force) and not os.path.isfile(file_hash_path):
        raise DownloadException(f"Unable to download '{hash_file}'")
    if not hash_file_check(file_hash_path, get_data_dir()) and not download_file(filename, force):
        raise DownloadException(f"Unable to download {filename}")
    return file_path


def get_list(filename: str) -> dict:
    with open(upgrade_list_or_do_nothing(filename), "r") as file:
        ret_list = {}
        try:
            ret_list = ic(json.loads(file.read()))
        except json.decoder.JSONDecodeError as e:
            typer.echo(f"Error: Invalid {filename} file\n{e}")
        finally:
            return ret_list


def get_whitelist() -> None:
    global whitelist
    ret_list = get_list(whitelist_file)
    if len(ret_list) < 1:
        return
    whitelist = ret_list


def get_blacklist() -> None:
    global blacklist
    ret_list = get_list(blacklist_file)
    if len(ret_list) < 1:
        return
    blacklist = ret_list


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


def get_actual_url(url: str, only_one: bool = False) -> str | None:
    if url is None:
        raise NoneUrlException("URL is None")
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
    new_url = ic(parsed_url.with_query(new_query_params).human_repr())
    try:
        response = ic(requests.head(new_url))
        if ic(response.status_code) in redirection_status_codes:
            headers = ic(response.headers)
            if only_one:
                return ic(headers["location"])
            return get_actual_url(ic(headers["location"]))
        return new_url
    except Exception as e:
        typer.echo(f"Error: {e}")
        return None


@app.command(help="Updates the whitelist and blacklist files.")
def list_update(debug: bool = False) -> None:
    """
    Updates the whitelist and blacklist files by forcing their upgrade process. Optionally provides debug 
    output based on the given flag.

    :param debug: Enables or disables debug mode. Defaults to False.
    """
    debug_output_control(debug)
    upgrade_list_or_do_nothing(whitelist_file, True)
    upgrade_list_or_do_nothing(blacklist_file, True)
    typer.echo("Force list updated")


@app.command(help="Cleans a given URL and copies it to the system clipboard.")
def clean_url(url: str, download_interval: int = 3600, debug: bool = False):
    """
    Cleans a given URL, copies it to the system clipboard, and outputs the cleaned 
    URL. The function also sets a global download interval and handles debug 
    message control.

    :param url: The URL string that needs to be cleaned.
    :param download_interval: The interval in seconds between downloads. Defaults to 3600.
    :param debug: Enables or disables debug mode. Defaults to False.
    """
    global global_download_interval
    debug_output_control(debug)
    global_download_interval = download_interval
    the_clean_url = get_clean_url(url)
    pyperclip.copy(the_clean_url)
    typer.echo(f"Cleaned URL: {the_clean_url}")
    typer.echo(f"Copied to clipboard")


@app.command(help="Fetches and processes the query parameters from the given URL.")
def fetch_url_query_params(url: str, download_interval: int = 3600, debug: bool = False):
    """
    Fetches and processes query parameters from the given URL. The function resolves
    an actual URL if redirects are present, parses it, and extracts the query
    parameters to display. Additionally, it allows customization of the download
    interval and toggles debugging output for logging purposes.

    :param url: The URL to fetch and process query parameters from.
    :param download_interval: The interval in seconds between downloads. Defaults to 3600.
    :param debug: Enables or disables debug mode. Defaults to False.
    """
    global global_download_interval
    debug_output_control(debug)
    global_download_interval = download_interval
    actual_url = get_actual_url(url, True)
    if actual_url is None:
        typer.echo(f"Error: Unable to get actual URL of {url}")
        typer.Exit(code=1)
        return
    parsed_url = ic(URL(actual_url))
    ret_list = [str(x) for x in parsed_url.query.items()]
    typer.echo(f"Fetched URL query params: {", ".join(ret_list)}")


@app.command(help="Fetches and processes the true URL for a given input URL.")
def fetch_true_url(url: str, only_fetch: bool = False, download_interval: int = 3600, debug: bool = False):
    """
    Fetches and processes the true URL for a given input URL. This function retrieves the
    actual URL, cleans it if necessary, and copies the final URL to the clipboard.
    The operation can be performed in a "fetch-only" mode or include URL cleaning.
    Additionally, it includes debug options and customizable download intervals.

    :param url: The original URL to process.
    :param only_fetch: Flag to decide whether to only fetch the actual URL or also clean it. Defaults to False.
    :param download_interval: The interval in seconds between downloads. Defaults to 3600.
    :param debug: Enables or disables debug mode. Defaults to False.
    """
    global global_download_interval
    debug_output_control(debug)
    global_download_interval = download_interval
    actual_url = get_actual_url(url)
    if actual_url is None:
        typer.echo(f"Error: Unable to get actual URL of {url}")
        typer.Exit(code=1)
        return
    return_url = actual_url if only_fetch else get_clean_url(actual_url)
    pyperclip.copy(return_url)
    typer.echo(f"Cleaned URL: {return_url}")
    typer.echo(f"Copied to clipboard")


@app.command(help="Monitors the clipboard for URLs and processes them to generate cleaned URLs or fetch actual URLs.")
def clipboard_watchers(only_fetch: bool = False, sleep_seconds: float = 1, download_interval: int = 3600,
                       debug: bool = False):
    """
    Monitors the clipboard for URLs and processes them to generate cleaned URLs or fetch actual URLs,
    depending on the specified options.

    The function runs indefinitely in a loop, checking the clipboard for changes and ensuring the
    content is processed only if it contains a valid URL and is new.

    :param only_fetch: If True, fetches the actual URL instead of cleaning it. Defaults to False.
    :param sleep_seconds: Time interval (in seconds) to wait between successive clipboard checks. Defaults to 1.
    :param download_interval: The interval in seconds between downloads. Defaults to 3600.
    :param debug: Enables or disables debug mode. Defaults to False.
    """
    global global_download_interval
    debug_output_control(debug)
    global_download_interval = download_interval
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


if __name__ == "__main__":
    app()
