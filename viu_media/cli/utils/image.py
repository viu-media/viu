import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from viu_media.core.exceptions import DependencyNotFoundError
import importlib.util

import click
import httpx

logger = logging.getLogger(__name__)


def resize_image_from_url(
    client: httpx.Client,
    url: str,
    new_width: int,
    new_height: int,
    output_path: Optional[Path] = None,
    maintain_aspect_ratio: bool = False,
    return_bytes: bool = True,
) -> bytes | None:
    """
    Fetches an image from a URL using a provided synchronous httpx.Client,
    resizes it with Pillow. Can either save the resized image to a file
    or return its bytes.

    Args:
        client (httpx.Client): An initialized synchronous httpx.Client instance.
        url (str): The URL of the image.
        new_width (int): The desired new width of the image.
        new_height (int): The desired new height of the image.
        output_path (str, optional): The path to save the resized image.
                                     Required if return_bytes is False.
        maintain_aspect_ratio (bool, optional): If True, resizes while maintaining
                                                the aspect ratio using thumbnail().
                                                Defaults to False.
        return_bytes (bool, optional): If True, returns the resized image as bytes.
                                       If False, saves to output_path. Defaults to False.

    Returns:
        bytes | None: The bytes of the resized image if return_bytes is True,
                      otherwise None.
    """
    from io import BytesIO

    if importlib.util.find_spec("PIL"):
        from PIL import Image  # pyright: ignore[reportMissingImports]

        if not return_bytes and output_path is None:
            raise ValueError("output_path must be provided if return_bytes is False.")

        try:
            # Use the provided synchronous client
            response = client.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes

            image_bytes = response.content
            image_stream = BytesIO(image_bytes)
            img = Image.open(image_stream)

            if maintain_aspect_ratio:
                img_copy = img.copy()
                img_copy.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                resized_img = img_copy
            else:
                resized_img = img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )

            if return_bytes:
                # Determine the output format. Default to JPEG if original is unknown or problematic.
                # Handle RGBA to RGB conversion for JPEG output.
                output_format = (
                    img.format if img.format in ["JPEG", "PNG", "WEBP"] else "JPEG"
                )
                if output_format == "JPEG":
                    if resized_img.mode in ("RGBA", "P"):
                        resized_img = resized_img.convert("RGB")

                byte_arr = BytesIO()
                resized_img.save(byte_arr, format=output_format)
                logger.info(
                    f"Image from {url} resized to {resized_img.width}x{resized_img.height} and returned as bytes ({output_format} format)."
                )
                return byte_arr.getvalue()
            else:
                # Ensure the directory exists before saving
                if output_path:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    resized_img.save(output_path)
                    logger.info(
                        f"Image from {url} resized to {resized_img.width}x{resized_img.height} and saved as '{output_path}'"
                    )
                    return None

        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {url}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            )
            return None
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
    else:
        raise DependencyNotFoundError(
            "Pillow library is required for image processing. Please install it via 'uv pip install Pillow'."
        )


def render(url: str, capture: bool = False, size: str = "30x30") -> Optional[str]:
    """
    Renders an image from a URL in the terminal using icat or chafa.

    This function automatically detects the best available tool.

    Args:
        url: The URL of the image to render.
        capture: If True, returns the terminal-formatted image as a string
                 instead of printing it. Defaults to False.
        size: The size parameter to pass to the rendering tool (e.g., "WxH").

    Returns:
        If capture is True, returns the image data as a string.
        If capture is False, prints directly to the terminal and returns None.
        Returns None on any failure.
    """
    # --- Try icat (Kitty terminal) first ---
    if icat_executable := shutil.which("icat"):
        process = subprocess.run(
            [icat_executable, "--align", "left", url],
            capture_output=capture,
            text=capture,
        )
        if process.returncode == 0:
            return process.stdout if capture else None
        logger.warning(f"icat failed for URL {url} with code {process.returncode}")

    # --- Fallback to chafa ---
    if chafa_executable := shutil.which("chafa"):
        try:
            # Chafa requires downloading the image data first
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=20)
                response.raise_for_status()
                img_bytes = response.content

            process = subprocess.run(
                [chafa_executable, f"--size={size}", "-"],
                capture_output=capture,
                text=capture,
                input=img_bytes,
            )
            if process.returncode == 0:
                return process.stdout if capture else None
            logger.warning(f"chafa failed for URL {url} with code {process.returncode}")

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching image for chafa: {e.response.status_code}"
            )
            click.echo(
                f"[dim]Error fetching image: {e.response.status_code}[/dim]", err=True
            )
        except Exception as e:
            logger.error(f"An exception occurred while running chafa: {e}")

        return None

    # --- Final fallback if no tool is found ---
    if not capture:
        # Only show this message if the user expected to see something.
        click.echo(
            "[dim](Image preview skipped: icat or chafa not found)[/dim]", err=True
        )

    return None
