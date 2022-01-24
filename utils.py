import json
import functools
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from aiohttp import (
    ClientSession,
)

class repr_json:
    def __init__(self, val):
        self.val = val

    def __repr__(self) -> str:
        if isinstance(self.val, str):
            return self.val
        return json.dumps(self.val, indent=4)

def flatten(args):
    for arg in args:
        if isinstance(arg, (list, tuple)):
            yield from flatten(arg)
        else:
            yield arg

def print_ext(
    *msg,
    color: str = None,
    label: str = None,
    prefix: str = None,
    indent: int = None,
    **kwargs,
):
    prefix_str = prefix or ""
    if indent:
        prefix_str += " " * indent
    if color:
        msg = [(color, " ".join(map(str, msg)))]
        if prefix_str:
            msg.insert(0, ("", prefix_str + " "))
        if label:
            msg.insert(0, ("fg:ansimagenta", label + "\n"))
        print_formatted_text(FormattedText(msg), **kwargs)
        return
    if label:
        print(label, **kwargs)
    if prefix_str:
        msg = (prefix_str, *msg)
    print(*msg, **kwargs)

def log_msg(*msg, color="fg:ansimagenta", **kwargs):
    run_in_terminal(lambda: print_ext(*msg, color=color, **kwargs))

async def get_genesis_file(genesis_url):
    genesis = None
    try:
        if genesis_url:
            async with ClientSession() as session:
                async with session.get(genesis_url) as resp:
                    genesis = await resp.text()
    except Exception:
        print("Error loading genesis transactions:")
    return genesis

def output_reader(handle, callback, *args, **kwargs):
    for line in iter(handle.readline, b""):
        if not line:
            break
        run_in_terminal(functools.partial(callback, line, *args))

def convert_to_http(name: str, port = None, path: str = None):
    if name.startswith("http://") or name.startswith("https://"):
        url = name
    else:
        url = f"http://{name}"
    if port:
        url = f"{url}:{str(port)}" 
    if path:
        url = f"{url}/{path}"
    return url
