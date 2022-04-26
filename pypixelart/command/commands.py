import logging
from dataclasses import dataclass
from typing import Tuple

import pygame as pg

from pypixelart.command import Command
from pypixelart.symmetry_type import SymmetryType
from pypixelart.utils import draw_pixel


@dataclass
class DrawPixelAtCursor(Command):
    image: pg.Surface
    position: Tuple[int, int]
    new_color: pg.Color
    symmetry_type: SymmetryType
    previous_pos_and_colors: Tuple[
        Tuple[Tuple[int, int], pg.Color], Tuple[Tuple[int, int], pg.Color]
    ] = None

    def execute(self) -> None:
        previous_pos_and_color = self.position, self.image.get_at(self.position)
        symmetric_previous_pos_and_color = draw_pixel(
            self.image, self.position, self.new_color, self.symmetry_type
        )
        self.previous_pos_and_colors = (
            previous_pos_and_color,
            symmetric_previous_pos_and_color,
        )
        logging.debug(
            f"Pixel drawn at position-color tuples: "
            f"{previous_pos_and_color} and "
            f"{symmetric_previous_pos_and_color}"
        )

    def undo(self) -> None:
        for drawn_pixel_pos_color_tuple in self.previous_pos_and_colors:
            # Second pixel could be None when the symmetry type is NoSymmetry
            if drawn_pixel_pos_color_tuple is not None:
                drawn_pixel_pos, drawn_pixel_color = drawn_pixel_pos_color_tuple
                self.image.set_at(drawn_pixel_pos, drawn_pixel_color)
                logging.debug(
                    f"Undo for position-color tuple {drawn_pixel_pos_color_tuple}"
                )

    def redo(self) -> None:
        self.execute()
