import functools
import logging
import os
import re
from itertools import cycle

logger = logging.getLogger(__name__)

# Dictionary to map hex values to characters
hex_to_char = {
    "01": "9",
    "08": "0",
    "05": "=",
    "0a": "2",
    "0b": "3",
    "0c": "4",
    "07": "?",
    "00": "8",
    "5c": "d",
    "0f": "7",
    "5e": "f",
    "17": "/",
    "54": "l",
    "09": "1",
    "48": "p",
    "4f": "w",
    "0e": "6",
    "5b": "c",
    "5d": "e",
    "0d": "5",
    "53": "k",
    "1e": "&",
    "5a": "b",
    "59": "a",
    "4a": "r",
    "4c": "t",
    "4e": "v",
    "57": "o",
    "51": "i",
}


def debug_extractor(extractor_function):
    @functools.wraps(extractor_function)
    def _provider_function_wrapper(*args):
        if not os.environ.get("VIU_DEBUG"):
            try:
                return extractor_function(*args)
            except Exception as e:
                logger.error(
                    f"[AllAnime@Server={args[3].get('sourceName', 'UNKNOWN')}]: {e}"
                )
        else:
            return extractor_function(*args)

    return _provider_function_wrapper


def give_random_quality(links):
    qualities = cycle(["1080", "720", "480", "360"])

    return [
        {**episode_stream, "quality": quality}
        for episode_stream, quality in zip(links, qualities, strict=False)
    ]


def one_digit_symmetric_xor(password: int, target: str):
    def genexp():
        for segment in bytearray.fromhex(target):
            yield segment ^ password

    return bytes(genexp()).decode("utf-8")


def decode_hex_string(hex_string):
    """some of the sources encrypt the urls into hex codes this function decrypts the urls

    Args:
        hex_string ([TODO:parameter]): [TODO:description]

    Returns:
        [TODO:return]
    """
    # Split the hex string into pairs of characters
    hex_pairs = re.findall("..", hex_string)

    # Decode each hex pair
    decoded_chars = [hex_to_char.get(pair.lower(), pair) for pair in hex_pairs]

    # TODO: Better type handling
    return "".join(decoded_chars)  # type: ignore
