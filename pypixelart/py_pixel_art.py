import logging
import pathlib
import sys

import click
import pygame as pg

from pypixelart.keybinding import KeyBinding
from pypixelart.symmetry_type import SymmetryType
from pypixelart.utils import (
    draw_keybindings,
    draw_grid,
    draw_help_keybind,
    draw_header_text,
    draw_resized_image,
    draw_rect_around_resized_img,
    draw_symmetry_line,
    draw_selected_color,
    draw_color_selection,
    draw_cursor_coordinates,
    handle_input,
)
from pypixelart.constants import (
    GREY,
    BLACK,
    WHITE,
    ALPHA,
    LIGHTER_GREY,
    DEFAULT_BORDER_RADIUS,
)


class PyPixelArt:
    def __init__(self, image: pg.Surface, path: pathlib.Path):
        logging.info(f"Instantiated PyPixelArt with path {path}")

        self.image, self.path = image, path

        window_width, window_height = 600, 600
        self.screen = pg.display.set_mode((window_width, window_height), pg.RESIZABLE)
        self.app_name = click.get_current_context().command.name
        pg.display.set_caption(self.app_name)

        self.cursor_position = pg.Vector2(0, 0)
        self.cursor_draw_color = WHITE

        self.resized_img_rect = self.last_resized_img_rect = None

        self.resized_img = self.rectangle_rect = None

        self.line_width = 4
        self.cursor_line_width = self.line_width // 2
        self.grid_line_width = 1
        self.symmetry_line_width = 4

        self.clock = pg.time.Clock()

        """
        Get the biggest image dimension and take the inverse rule of 
        three between the corresponding window dimension, 100 and the 
        image dimension to get the appropriate zoom that keeps the 
        image in the screen
        """
        if image.get_width() > image.get_height():
            logging.debug(
                f"Image width {image.get_width()} > image height {image.get_height()}"
            )
            initial_zoom_percent = (window_width * 100) // image.get_width()
            logging.debug(f"Zoom initialized to {initial_zoom_percent}")
        else:
            logging.debug(
                f"Image width {image.get_width()} <= image height {image.get_height()}"
            )
            initial_zoom_percent = (window_height * 100) // image.get_height()
            logging.debug(f"Zoom initialized to {initial_zoom_percent}")

        # Percent of zoom space that must be left for the rest of the UI
        margin_percent = 20
        # Remove margin_percent percent of the zoom value to leave room for the UI
        initial_zoom_percent = (initial_zoom_percent * (100 - margin_percent)) // 100
        logging.debug(
            f"Changed initial zoom to {initial_zoom_percent} after removing the {margin_percent}% margin for the UI"
        )

        # Set the step to 5% of the zoom
        zoom_step_percent = initial_zoom_percent // 20
        # Set it to 1 if the result of the division above was 0
        zoom_step_percent = 1 if zoom_step_percent == 0 else zoom_step_percent
        logging.debug(f"Zoom step initialized to {zoom_step_percent}")

        self.zoom = {
            "percent": initial_zoom_percent,
            "step": zoom_step_percent,
            "changed": False,
        }

        self.grid = False
        self.color_selection = False
        self.show_bindings = False

        self.symmetry = SymmetryType.NoSymmetry

        self.image_history = list()

        self.palette_colors = {
            "red": pg.Color(172, 50, 50),
            "cream": pg.Color(217, 160, 102),
            "brown": pg.Color(102, 57, 49),
            "black": pg.Color(0, 0, 0),
            "blue": pg.Color(91, 110, 225),
            "yellow": pg.Color(251, 242, 54),
        }

        self.help_keybinding = KeyBinding(
            pg.K_SPACE, "Help", lambda: self.set_show_bindings()
        )

        zoom_g, cursor_g = "Zoom", "Move Cursor"
        self.keybindings = [
            KeyBinding(pg.K_i, "Draw", self.draw_pixel, on_pressed=True),
            KeyBinding(pg.K_x, "Erase", self.erase_pixel, on_pressed=True),
            KeyBinding(pg.K_u, "Undo", self.undo),
            KeyBinding(pg.K_w, "Save file", self.save),
            KeyBinding(pg.K_n, zoom_g, lambda: self.set_zoom(True), on_pressed=True),
            KeyBinding(pg.K_b, zoom_g, lambda: self.set_zoom(False), on_pressed=True),
            KeyBinding(pg.K_k, cursor_g, lambda: self.move_cursor(0, -1)),
            KeyBinding(pg.K_j, cursor_g, lambda: self.move_cursor(0, 1)),
            KeyBinding(pg.K_l, cursor_g, lambda: self.move_cursor(1, 0)),
            KeyBinding(pg.K_h, cursor_g, lambda: self.move_cursor(-1, 0)),
            KeyBinding(pg.K_g, "Grid", self.set_grid),
            KeyBinding(pg.K_s, "Symmetry", self.set_symmetry),
            KeyBinding(pg.K_ESCAPE, "Exit", sys.exit),
            KeyBinding(pg.K_c, "Color selection", self.set_color_selection),
        ]

        self.keybindings += [
            KeyBinding(
                pg.key.key_code(str(i)),
                "Color",
                lambda c=color: self.set_cursor_color(c),
            )
            for i, (name, color) in enumerate(self.palette_colors.items(), start=1)
        ]

        self.keybindings += [self.help_keybinding]

    def set_zoom(self, add_zoom: bool):
        to_add = self.zoom["step"] if add_zoom else -self.zoom["step"]
        if self.zoom["percent"] + to_add > 0:
            self.zoom["changed"] = True
            self.zoom["percent"] += to_add
            logging.debug(f"Zoom changed by {to_add} to {self.zoom['percent']}")

    def move_cursor(self, x: int, y: int):
        """
        Add x and y to existing coordinates and divide by width/height to avoid going out of grid.
        When added x at the end, goes back to beginning. When subtracting at x=0, goes to the end.
        Same applies for y.
        """
        new_x = (self.cursor_position.x + x) % self.image.get_width()
        new_y = (self.cursor_position.y + y) % self.image.get_height()
        self.cursor_position.update(new_x, new_y)
        logging.debug(f"Cursor position updated to ({new_x}, {new_y})")

    def set_grid(self):
        self.grid = not self.grid
        logging.debug(f"Grid set to {self.grid}")

    def set_symmetry(self):
        self.symmetry = SymmetryType(
            (self.symmetry.value + 1) % len(list(SymmetryType))
        )
        logging.debug(f"Symmetry set to {self.symmetry.name}")

    def set_color_selection(self):
        self.color_selection = not self.color_selection
        logging.debug(f"Color selection set to {self.color_selection}")

    def set_show_bindings(self):
        self.show_bindings = not self.show_bindings
        logging.debug(f"Show bindings set to {self.show_bindings}")

    def set_cursor_color(self, selected_color: pg.Color):
        self.color_selection = False
        self.cursor_draw_color = selected_color
        logging.debug(f"Cursor color set to {self.cursor_position}")

    def draw_pixel(self):
        cursor_x, cursor_y = map(int, self.cursor_position)

        if self.image.get_at((cursor_x, cursor_y)) == self.cursor_draw_color:
            logging.debug(
                f"Tried to draw pixel at {(cursor_x, cursor_y)} but it has the same color {self.cursor_draw_color}, "
                f"returning from draw_pixel"
            )
            return

        self.image_history.append(self.image.copy())
        self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)
        logging.debug(
            f"Drew pixel at {(cursor_x, cursor_y)} with color {self.cursor_draw_color}"
        )
        logging.debug(
            f"After the current pixel, image history has {len(self.image_history)} elements"
        )

        if self.symmetry == SymmetryType.NoSymmetry:
            logging.debug(f"No symmetry is set, returning from draw_pixel")
            return

        middle_w, middle_h = self.image.get_width() // 2, self.image.get_height() // 2
        logging.debug(f"Grid symmetry middle width: {middle_w}")
        logging.debug(f"Grid symmetry middle height: {middle_h}")

        if self.symmetry == SymmetryType.Vertical:

            cursor_x = middle_w + (middle_w - cursor_x) - 1
            self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)
        elif self.symmetry == SymmetryType.Horizontal:

            cursor_y = middle_h + (middle_h - cursor_y) - 1
            self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)

        logging.debug(
            f"Drew {self.symmetry.name} symmetry pixel at {(cursor_x, cursor_y)} with color {self.cursor_draw_color}"
        )

    def erase_pixel(self):
        cursor_x, cursor_y = map(int, self.cursor_position)

        if self.image.get_at((cursor_x, cursor_y)) == ALPHA:
            return

        self.image_history.append(self.image.copy())
        self.image.set_at((cursor_x, cursor_y), ALPHA)
        logging.debug(f"Erased pixel at {(cursor_x, cursor_y)}")
        logging.debug(
            f"After the current erase, image history has {len(self.image_history)} elements"
        )

    def undo(self):
        if self.image_history:
            saved_img: pg.Surface = self.image_history.pop()
            self.image.fill(ALPHA)
            self.image.blit(saved_img, (0, 0), saved_img.get_rect())

    def save(self):
        pg.image.save(self.image, self.path)
        click.echo(f"Saved {self.path}")

    def run_loop(self):
        logging.info("Running loop")

        while True:
            self.screen.fill(GREY)

            draw_header_text(
                app_name=self.app_name,
                path_name=self.path.name,
                width=self.image.get_width(),
                height=self.image.get_height(),
                zoom=self.zoom["percent"],
            )

            self.last_resized_img_rect = self.resized_img_rect

            # Sets a light grey color for the alpha background of the resized image
            if self.resized_img_rect:
                pg.draw.rect(
                    pg.display.get_surface(),
                    LIGHTER_GREY,
                    self.resized_img_rect,
                    border_radius=DEFAULT_BORDER_RADIUS,
                )

            self.resized_img, self.resized_img_rect = draw_resized_image(
                self.image, self.zoom["percent"]
            )

            self.rectangle_rect = draw_rect_around_resized_img(
                self.resized_img, self.resized_img_rect, self.line_width
            )

            cursor_width = self.resized_img_rect.w / self.image.get_rect().w
            cursor_height = self.resized_img_rect.h / self.image.get_rect().h
            cursor_x, cursor_y = map(int, self.cursor_position)
            cursor_rect_xy = (
                cursor_width * cursor_x + self.resized_img_rect.x,
                cursor_height * cursor_y + self.resized_img_rect.y,
            )
            cursor_rect = (pg.Rect(cursor_rect_xy, (cursor_width, cursor_height)),)

            if self.grid:
                where = self.resized_img.get_rect().move(
                    (self.resized_img_rect.x, self.resized_img_rect.y)
                )
                draw_grid(
                    where, (int(cursor_width), int(cursor_height)), self.grid_line_width
                )

            draw_symmetry_line(
                self.symmetry,
                self.resized_img.get_rect().move(
                    (self.resized_img_rect.x, self.resized_img_rect.y)
                ),
                self.symmetry_line_width,
            )

            cursor_image_color = BLACK if self.grid else WHITE
            pg.draw.rect(
                self.screen,
                cursor_image_color,
                cursor_rect,
                width=self.cursor_line_width,
            )

            cursor_coords_text_rect = draw_cursor_coordinates(
                (cursor_x, cursor_y), self.rectangle_rect.topleft
            )

            rect_top_right_corner_x, _ = self.rectangle_rect.topright
            draw_selected_color(
                self.cursor_draw_color,
                rect_top_right_corner_x=rect_top_right_corner_x,
                cursor_coord_text_y=cursor_coords_text_rect.y,
            )

            handle_input(self.keybindings)

            if self.show_bindings:
                draw_keybindings(self.keybindings, self.line_width)
            else:
                draw_help_keybind(self.help_keybinding, self.rectangle_rect)

            if self.color_selection:
                draw_color_selection(self.palette_colors, self.line_width)

            pg.display.flip()

            self.clock.tick(60)
