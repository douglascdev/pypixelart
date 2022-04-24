import logging

import click
import pygame as pg
import pygame.font

from pypixelart.py_pixel_art import PyPixelArt
from pypixelart.utils import *


def print_welcome_msg(func):
    """
    Print a welcome message. Uses a decorator to ensure it executes before click and therefore always shows the message
    """

    def wrapper():
        click.clear()
        click.echo(
            click.style("PyPixelArt - A keyboard-centric pixel editor", fg="red")
        )
        func()

    return wrapper


@print_welcome_msg
@click.command(name="PyPixelArt")
@click.option(
    "--filepath",
    "-f",
    prompt="File path",
    help="Path for the file you want to open",
    type=click.Path(),
)
@click.option(
    "--resolution",
    "-res",
    help="Image height and width separated by a comma, e.g. 20,10 for a 20x10 image. Note that no spaces can be used.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print debug-level logging to standard output",
)
def main(filepath, resolution, debug):
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s",
        level=level,
    )
    logging.info(f"Called with arguments '{filepath}' and '{resolution}'")

    pg.init()

    path = Path(filepath)
    if path.exists() and path.is_file():
        logging.info(f"Path '{path}' exists and is file. Now loading as image.")
        image = pg.image.load(path)
    else:
        logging.info("No valid path was provided, creating new surface.")

        if resolution:
            img_size = tuple(map(int, resolution.split(",")))
            logging.info(f"Resolution {img_size} loaded from click argument")
        else:
            width = int(input("Image width: "))
            height = int(input("Image height: "))
            img_size = width, height
            logging.info(f"Resolution {img_size} loaded from input")

        image = pg.Surface(img_size, pygame.SRCALPHA)

    pypixelart = PyPixelArt(image, path)
    pypixelart.run_loop()


if __name__ == "__main__":
    main()
