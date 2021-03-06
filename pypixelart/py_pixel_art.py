import logging
import pathlib
import sys

import click
import pygame as pg

from pypixelart.command.commands import DrawPixelAtCursor
from pypixelart.command.controller import CommandController
from pypixelart.keybinding import KeyBinding
from pypixelart.point import Point
from pypixelart.symmetry_type import SymmetryType
from pypixelart.utils import (
    draw_keybindings,
    draw_grid,
    draw_help_keybind,
    draw_header_text,
    draw_scaled_image,
    draw_rect_around_resized_img,
    draw_symmetry_line,
    draw_selected_color,
    draw_color_selection,
    draw_cursor_coordinates,
)
from pypixelart.constants import (
    GREY,
    BLACK,
    WHITE,
    LIGHTER_GREY,
    DEFAULT_BORDER_RADIUS,
    ALPHA,
)


class PyPixelArt:
    """
    PyPixelArt controls all the behaviour of the application. It keeps track of the state of the image and UI,
    calls the corresponding methods when a keybinding is called, draws the UI on the screen, etc.
    """

    def __init__(self, image: pg.Surface, path: pathlib.Path):
        logging.info(f"Instantiated PyPixelArt with path {path}")

        self.image: pg.Surface = image
        self.path: pathlib.Path = path

        window_width: int = 600
        window_height: int = 600

        self.screen: pg.Surface = pg.display.set_mode(
            (window_width, window_height), pg.RESIZABLE
        )
        self.app_name: str = click.get_current_context().command.name

        pg.display.set_caption(self.app_name)

        self.cursor_position: Point = Point(0, 0)
        self.cursor_draw_color: pg.Color = WHITE

        self.resized_img_rect: pg.Rect = None
        self.last_resized_img_rect: pg.Rect = None

        self.resized_img: pg.Surface = None
        self.rectangle_rect: pg.Rect = None

        self.line_width: int = 4
        self.cursor_line_width: int = self.line_width // 2
        self.grid_line_width: int = 1
        self.symmetry_line_width: int = 4
        self.command_controller: CommandController = CommandController()

        self.clock: pg.time.Clock = pg.time.Clock()

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

        # Boolean variables checked in the run_loop method to determine which elements to draw in the screen
        self.is_drawing_grid = False
        self.is_drawing_color_selection = False
        self.is_drawing_bindings = False

        # Symmetry allows mirroring horizontally or vertically the changes done to the image
        self.symmetry = SymmetryType.NoSymmetry

        # The palette of colors seen in color selection
        self.palette_colors = {
            "red": pg.Color(172, 50, 50),
            "cream": pg.Color(217, 160, 102),
            "brown": pg.Color(102, 57, 49),
            "black": pg.Color(0, 0, 0),
            "blue": pg.Color(91, 110, 225),
            "yellow": pg.Color(251, 242, 54),
        }

        """ 
        Maps keycodes to the group they're displayed as on the help menu and 
        the function it should call when the button is pressed
        """
        self.keybindings = [
            KeyBinding(pg.K_i, "Draw", self.draw_pixel),
            KeyBinding(pg.K_x, "Erase", self.erase_pixel),
            KeyBinding(pg.K_u, "Undo", self.undo),
            KeyBinding(pg.K_r, "Redo", self.redo),
            KeyBinding(pg.K_w, "Save file", self.save),
            KeyBinding(pg.K_n, "Zoom", lambda: self.set_zoom(True), on_pressed=True),
            KeyBinding(pg.K_b, "Zoom", lambda: self.set_zoom(False), on_pressed=True),
            KeyBinding(pg.K_k, "Move cursor", lambda: self.move_cursor(0, -1)),
            KeyBinding(pg.K_j, "Move cursor", lambda: self.move_cursor(0, 1)),
            KeyBinding(pg.K_l, "Move cursor", lambda: self.move_cursor(1, 0)),
            KeyBinding(pg.K_h, "Move cursor", lambda: self.move_cursor(-1, 0)),
            KeyBinding(pg.K_g, "Grid", self.toggle_grid),
            KeyBinding(pg.K_s, "Symmetry", self.set_symmetry),
            KeyBinding(pg.K_q, "Exit", sys.exit),
            KeyBinding(pg.K_c, "Color selection", self.toggle_color_selection),
        ]

        """
        Create a keybinding object for every color in the palette and assign a numeric
        keycode starting from 1. Each number sets the current color to a color in the
        palette.
        """
        self.keybindings += [
            KeyBinding(
                pg.key.key_code(str(i)),
                "Color",
                lambda c=color: self.set_cursor_color(c),
            )
            for i, (name, color) in enumerate(self.palette_colors.items(), start=1)
        ]

        self.help_keybinding = KeyBinding(pg.K_SPACE, "Help", self.toggle_show_bindings)

        self.keybindings += [self.help_keybinding]

    def set_zoom(self, is_positive_step: bool):
        """
        Add one self.zoom["step"] percent of zoom if is_positive_step is True or subtract it
        if is_positive_zoom is False
        """
        to_add = self.zoom["step"] if is_positive_step else -self.zoom["step"]
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
        self.cursor_position = Point(new_x, new_y)
        logging.debug(f"Cursor position updated to ({new_x}, {new_y})")

    def set_symmetry(self):
        self.symmetry = SymmetryType(
            (self.symmetry.value + 1) % len(list(SymmetryType))
        )
        logging.debug(f"Symmetry set to {self.symmetry.name}")

    def toggle_grid(self):
        """
        Toggle value of is_drawing_grid to determine whether to draw the grid
        """
        self.is_drawing_grid = not self.is_drawing_grid
        logging.debug(f"Grid set to {self.is_drawing_grid}")

    def toggle_color_selection(self):
        """
        Toggle value of is_drawing_color_selection to determine whether to draw
        the color selection menu
        """
        self.is_drawing_color_selection = not self.is_drawing_color_selection
        logging.debug(f"Color selection set to {self.is_drawing_color_selection}")

    def toggle_show_bindings(self):
        """
        Toggle value of is_drawing_keybindings to determine whether to draw
        the menu that shows the available keybindings
        """
        self.is_drawing_bindings = not self.is_drawing_bindings
        logging.debug(f"Show bindings set to {self.is_drawing_bindings}")

    def set_cursor_color(self, selected_color: pg.Color):
        """
        Set the color used when drawing a pixel
        """
        self.is_drawing_color_selection = False
        self.cursor_draw_color = selected_color
        logging.debug(f"Cursor color set to {selected_color}")

    def draw_pixel(self):
        """
        Draw a pixel in the image using the selected position and color attributes
        """
        draw_command = DrawPixelAtCursor(
            self.image,
            self.cursor_position.coordinates,
            self.cursor_draw_color,
            self.symmetry,
        )
        self.command_controller.execute(draw_command)

    def erase_pixel(self):
        """
        Erase a pixel from the image using the selected position attributes.
        In other words, draw an ALPHA pixel at the position attribute.
        """
        erase_command = DrawPixelAtCursor(
            self.image, self.cursor_position.coordinates, ALPHA, self.symmetry
        )
        self.command_controller.execute(erase_command)

    def undo(self):
        """
        Undo the last command to change the image
        """
        self.command_controller.undo()

    def redo(self):
        """
        Redo the last command to be undone
        """
        self.command_controller.redo()

    def save(self):
        """
        Save the image to the file in the path attribute
        """
        pg.image.save(self.image, self.path)
        click.echo(f"Saved {self.path}")

    def handle_input(self):
        """
        Iterates over the list of Keybinding objects then for each of them, check if
        the keycode was pressed and call it's corresponding function
        """
        on_pressed_bindings = set(filter(lambda k: k.on_pressed, self.keybindings))
        for binding in on_pressed_bindings:
            if pg.key.get_pressed()[binding.keycode]:
                binding.func()

        not_on_pressed_keybindings = set(self.keybindings).difference(
            on_pressed_bindings
        )
        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()

            for binding in not_on_pressed_keybindings:
                if event.type == pg.KEYDOWN and event.key == binding.keycode:
                    binding.func()

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

            self.resized_img, self.resized_img_rect = draw_scaled_image(
                self.image, self.zoom["percent"]
            )

            self.rectangle_rect = draw_rect_around_resized_img(
                self.resized_img, self.resized_img_rect, self.line_width
            )

            cursor_width = self.resized_img_rect.w / self.image.get_rect().w
            cursor_height = self.resized_img_rect.h / self.image.get_rect().h
            cursor_rect_xy = (
                cursor_width * self.cursor_position.x + self.resized_img_rect.x,
                cursor_height * self.cursor_position.y + self.resized_img_rect.y,
            )
            cursor_rect = (pg.Rect(cursor_rect_xy, (cursor_width, cursor_height)),)

            if self.is_drawing_grid:
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

            cursor_image_color = BLACK if self.is_drawing_grid else WHITE
            pg.draw.rect(
                self.screen,
                cursor_image_color,
                cursor_rect,
                width=self.cursor_line_width,
            )

            cursor_coords_text_rect = draw_cursor_coordinates(
                self.cursor_position.coordinates, self.rectangle_rect.topleft
            )

            rect_top_right_corner_x, _ = self.rectangle_rect.topright
            draw_selected_color(
                self.cursor_draw_color,
                rect_top_right_corner_x=rect_top_right_corner_x,
                cursor_coord_text_y=cursor_coords_text_rect.y,
            )

            self.handle_input()

            if self.is_drawing_bindings:
                draw_keybindings(self.keybindings, self.line_width)
            else:
                draw_help_keybind(self.help_keybinding, self.rectangle_rect)

            if self.is_drawing_color_selection:
                draw_color_selection(self.palette_colors, self.line_width)

            pg.display.flip()

            self.clock.tick(60)
