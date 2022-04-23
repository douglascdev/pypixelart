import pathlib

import click
import pygame as pg
import pygame.font

from pypixelart.utils import *


class PyPixelArt:
    def __init__(self, image: pg.Surface, path: pathlib.Path):
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
            initial_zoom_percent = (window_width * 100) // image.get_width()
        else:
            initial_zoom_percent = (window_height * 100) // image.get_height()

        # Percent of zoom space that must be left for the rest of the UI
        margin_percent = 20
        # Remove margin_percent percent of the zoom value to leave room for the UI
        initial_zoom_percent = (initial_zoom_percent * (100 - margin_percent)) // 100

        step = initial_zoom_percent // 20  # Set the step to 5% of the zoom
        step = 1 if step == 0 else step  # Set it to 1 if the result of the division above was 0

        self.zoom = {
            "percent": initial_zoom_percent,
            "step": step,
            "changed": False,
        }

        self.grid = False
        self.color_selection = False
        self.show_bindings = False

        self.symmetry = SymmetryType.NoSymmetry

        self.image_history = list()

        self.help_keybinding = KeyBinding(
            pg.K_SPACE, "Help", lambda: self.set_show_bindings()
        )

        self.palette_colors = {
            "red": pg.Color(172, 50, 50),
            "cream": pg.Color(217, 160, 102),
            "brown": pg.Color(102, 57, 49),
            "black": pg.Color(0, 0, 0),
            "blue": pg.Color(91, 110, 225),
            "yellow": pg.Color(251, 242, 54),
        }

        zoom_g, cursor_g = "Zoom", "Move Cursor"
        self.keybindings = [
            KeyBinding(pg.K_i, "Draw", lambda: self.draw_pixel(), on_pressed=True),
            KeyBinding(pg.K_x, "Erase", lambda: self.erase_pixel(), on_pressed=True),
            KeyBinding(pg.K_u, "Undo", lambda: self.undo()),
            KeyBinding(pg.K_w, "Save file", lambda: self.save()),
            KeyBinding(pg.K_n, zoom_g, lambda: self.change_zoom(True), on_pressed=True),
            KeyBinding(
                pg.K_b, zoom_g, lambda: self.change_zoom(False), on_pressed=True
            ),
            KeyBinding(pg.K_k, cursor_g, lambda: self.move_cursor(0, -1)),
            KeyBinding(pg.K_j, cursor_g, lambda: self.move_cursor(0, 1)),
            KeyBinding(pg.K_l, cursor_g, lambda: self.move_cursor(1, 0)),
            KeyBinding(pg.K_h, cursor_g, lambda: self.move_cursor(-1, 0)),
            KeyBinding(pg.K_g, "Grid", lambda: self.set_grid()),
            KeyBinding(pg.K_s, "Symmetry", lambda: self.set_symmetry()),
            KeyBinding(pg.K_ESCAPE, "Exit", lambda: sys.exit()),
            KeyBinding(pg.K_c, "Color selection", lambda: self.set_color_selection()),
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

    def change_zoom(self, is_positive: bool):
        to_add = self.zoom["step"] if is_positive else -self.zoom["step"]
        if self.zoom["percent"] + to_add > 0:
            self.zoom["changed"] = True
            self.zoom["percent"] += to_add

    def move_cursor(self, x: int, y: int):
        """
        Add x and y to existing coordinates and divide by width/height to avoid going out of grid.
        When added x at the end, goes back to beginning. When subtracting at x=0, goes to the end.
        Same applies for y.
        """
        new_x = (self.cursor_position.x + x) % self.image.get_width()
        new_y = (self.cursor_position.y + y) % self.image.get_height()
        self.cursor_position.update(new_x, new_y)

    def set_grid(self):
        self.grid = not self.grid

    def set_symmetry(self):
        self.symmetry = SymmetryType(
            (self.symmetry.value + 1) % len(list(SymmetryType))
        )

    def set_color_selection(self):
        self.color_selection = not self.color_selection

    def set_show_bindings(self):
        self.show_bindings = not self.show_bindings

    def set_cursor_color(self, selected_color: pg.Color):
        self.color_selection = False
        self.cursor_draw_color = selected_color

    def draw_pixel(self):
        cursor_x, cursor_y = map(int, self.cursor_position)

        if self.image.get_at((cursor_x, cursor_y)) == self.cursor_draw_color:
            return

        self.image_history.append(self.image.copy())
        self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)

        if self.symmetry == SymmetryType.NoSymmetry:
            return

        middle_w, middle_h = self.image.get_width() // 2, self.image.get_height() // 2
        if self.symmetry == SymmetryType.Vertical:

            cursor_x = middle_w + (middle_w - cursor_x) - 1
            self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)
        elif self.symmetry == SymmetryType.Horizontal:

            cursor_y = middle_h + (middle_h - cursor_y) - 1
            self.image.set_at((cursor_x, cursor_y), self.cursor_draw_color)

    def erase_pixel(self):
        cursor_x, cursor_y = self.cursor_position

        if self.image.get_at((cursor_x, cursor_y)) == ALPHA:
            return

        self.image_history.append(self.image.copy())
        self.image.set_at((cursor_x, cursor_y), ALPHA)

    def undo(self):
        if self.image_history:
            saved_img: pg.Surface = self.image_history.pop()
            self.image.fill(ALPHA)
            self.image.blit(saved_img, (0, 0), saved_img.get_rect())

    def save(self):
        pg.image.save(self.image, self.path)
        click.echo(f"Saved {self.path}")

    def run_loop(self):

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
            self.resized_img, self.resized_img_rect = draw_resized_image(
                self.image, self.zoom["percent"]
            )

            self.rectangle_rect = draw_rect_around_resized_img(
                self.resized_img, self.resized_img_rect, self.line_width
            )

            cursor_width = self.resized_img_rect.w / self.image.get_rect().w
            cursor_height = self.resized_img_rect.h / self.image.get_rect().h
            cursor_x, cursor_y = map(int, self.cursor_position)
            cursor_rect_xy = (cursor_width * cursor_x + self.resized_img_rect.x, cursor_height * cursor_y + self.resized_img_rect.y)
            cursor_rect = pg.Rect(cursor_rect_xy, (cursor_width, cursor_height)),

            if self.grid:
                where = self.resized_img.get_rect().move(
                    (self.resized_img_rect.x, self.resized_img_rect.y)
                )
                draw_grid(where, (int(cursor_width), int(cursor_height)), self.grid_line_width)

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
def main(filepath, resolution):
    pg.init()

    path = Path(filepath)
    if path.exists() and path.is_file():
        image = pg.image.load(path)
    else:
        if resolution:
            img_size = tuple(map(int, resolution.split(",")))
        else:
            width = int(input("Image width: "))
            height = int(input("Image height: "))
            img_size = width, height

        image = pg.Surface(img_size, pygame.SRCALPHA)

    pypixelart = PyPixelArt(image, path)
    pypixelart.run_loop()


if __name__ == "__main__":
    main()
