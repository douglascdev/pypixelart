import itertools
import pathlib
import sys
from enum import IntEnum
from pathlib import Path
from typing import Tuple, Union, Callable, Iterable

import click
import pygame as pg
import pygame.font

black, white, grey, red = (
    pg.Color(20, 20, 20),
    pg.Color(255, 255, 255),
    pg.Color(50, 50, 50),
    pg.Color(150, 0, 0),
)


class SymmetryType(IntEnum):
    NoSymmetry = (0,)
    Horizontal = (1,)
    Vertical = (2,)


class KeyBinding:
    def __init__(self, keycode: int, group: str, func: Callable, on_pressed=False):
        self.keycode = keycode
        self.group = group
        self.func = func
        self.on_pressed = on_pressed

    def __str__(self):
        return f"(keycode={pg.key.name(self.keycode)}, group={self.group})"


def blit_text_to_screen(
    draw: Union[str, pg.Surface], coord: Union[Iterable, Tuple[int, int], pg.Rect]
):
    surface = draw if isinstance(draw, pg.Surface) else new_text_surface(str(draw))
    pg.display.get_surface().blit(surface, coord)


def draw_selected_color(
    color: pg.Color, rect_top_right_corner_x: int, cursor_coord_text_y: int
):
    selected_color_text = new_text_surface("Color: ", color=white)
    w, h = selected_color_text.get_width(), selected_color_text.get_height()
    selected_color_surface = pg.Surface(
        (
            w + h,
            h,
        ),
        pygame.SRCALPHA,
    )
    selected_color_surface.blit(selected_color_text, (0, 0))
    pg.draw.rect(
        selected_color_surface,
        color,
        pg.Rect(
            selected_color_text.get_rect().topright,
            (h, h),
        ),
    )
    pg.display.get_surface().blit(
        selected_color_surface,
        (
            rect_top_right_corner_x - w,
            cursor_coord_text_y,
        ),
    )


def draw_color_selection(palette_colors: dict, line_width: int):
    screen = pg.display.get_surface()
    palette_rect = pg.Rect((0, 0), (screen.get_width() // 2, screen.get_height() // 2))
    palette_surface = pg.Surface((palette_rect.w, palette_rect.h))
    palette_surface.fill(black)

    for i, name_color in enumerate(palette_colors.items(), start=1):
        name, color = name_color
        color_surface = pg.Surface((palette_rect.w // 10, palette_rect.h // 10))
        color_surface_rect = color_surface.get_rect()
        (
            color_surface_center_x,
            color_surface_center_y,
        ) = color_surface_rect.center
        pg.draw.rect(color_surface, color, color_surface_rect)
        color_binding_text = new_text_surface(str(i), color=~color)
        center_x = color_surface_center_x - color_binding_text.get_width() // 2
        center_y = color_surface_center_y - color_binding_text.get_height() // 2
        color_surface.blit(color_binding_text, (center_x, center_y))
        palette_surface.blit(color_surface, ((i - 1) * color_surface_rect.w, 0))

    pg.draw.rect(palette_surface, white, palette_rect, width=line_width)
    palette_rect.x, palette_rect.y = rect_screen_center(
        palette_rect, center_x=True, center_y=True
    )
    screen.blit(palette_surface, palette_rect)

    # Draws color selection title
    palette_mid_top_x, palette_mid_top_y = palette_rect.midtop
    selection_title_surface = new_text_surface("Color selection", color=white)
    selection_title_pos = (
        palette_mid_top_x - selection_title_surface.get_width() // 2,
        palette_mid_top_y - 20,
    )
    selection_title_size = (
        selection_title_surface.get_width(),
        selection_title_surface.get_height(),
    )
    selection_title_rect = pg.Rect(selection_title_pos, selection_title_size)
    blit_text_to_screen(selection_title_surface, selection_title_rect)


def draw_resized_image(image: pg.Surface, zoom: int) -> Tuple[pg.Surface, pg.Rect]:
    resized_img = resize_surface_by_percentage(image, zoom)
    resized_img_rect = pg.Rect(
        rect_screen_center(resized_img.get_rect(), center_x=True, center_y=True),
        (resized_img.get_width(), resized_img.get_height()),
    )
    pg.display.get_surface().blit(resized_img, resized_img_rect)
    return resized_img, resized_img_rect


def draw_symmetry_line(sym_type: SymmetryType, rect: pg.Rect, line_width: int):
    if sym_type == SymmetryType.NoSymmetry:
        return

    start_x, start_y = (
        rect.midtop if sym_type == SymmetryType.Vertical else rect.midleft
    )
    end_x, end_y = (
        rect.midbottom if sym_type == SymmetryType.Vertical else rect.midright
    )

    pg.draw.line(
        pg.display.get_surface(),
        black,
        (start_x, start_y),
        (end_x, end_y),
        width=line_width,
    )


def draw_grid(where: pg.Rect, size: Tuple[int, int], line_width: int):
    rectangles_w, rectangles_h = size
    for i, j in (
        (i, j)
        for i in range(where.x, where.x + where.w, rectangles_w)
        for j in range(where.y, where.y + where.h, rectangles_h)
    ):
        pg.draw.rect(
            pg.display.get_surface(),
            white,
            pg.Rect((i, j), (rectangles_w, rectangles_h)),
            width=line_width,
        )


def draw_header_text(**kwargs):
    app_name, path_name, width, height, zoom = (
        kwargs.get(arg) for arg in ("app_name", "path_name", "width", "height", "zoom")
    )
    header_text = f"{app_name}: {path_name} ({width}x{height}) {zoom}%"
    text_surface = new_text_surface(header_text, color=red)
    text_rect = rect_screen_center(text_surface.get_rect().move(0, 10), center_x=True)
    blit_text_to_screen(text_surface, text_rect)


def draw_rect_around_resized_img(
    resized_img: pg.Surface, resized_img_rect: pg.Rect, line_width: int
) -> pg.Rect:
    rectangle_x, rectangle_y = (
        resized_img_rect.x - line_width,
        resized_img_rect.y - line_width,
    )
    rectangle_w, rectangle_h = (
        resized_img.get_rect().w + line_width,
        resized_img.get_rect().h + line_width,
    )
    rectangle_rect = pg.Rect((rectangle_x, rectangle_y), (rectangle_w, rectangle_h))
    pg.draw.rect(pg.display.get_surface(), white, rectangle_rect, width=line_width)
    return rectangle_rect


def draw_cursor_coordinates(
    cursor_coords: Tuple[int, int], rectangle_top_left_coord: Tuple[int, int]
) -> pg.Rect:
    cursor_pixels_x, cursor_pixels_y = cursor_coords
    text = f"({cursor_pixels_x}, {cursor_pixels_y})"
    text_surface = new_text_surface(text, color=white)
    cursor_coords_text_rect = pg.Rect(
        rectangle_top_left_coord,
        (text_surface.get_width(), text_surface.get_height()),
    )
    cursor_coords_text_rect.move_ip(0, -20)
    blit_text_to_screen(text_surface, cursor_coords_text_rect)
    return cursor_coords_text_rect


def draw_keybindings(keybindings: Iterable[KeyBinding], line_width: int):
    screen = pg.display.get_surface()
    grouped_bindings = itertools.groupby(keybindings, lambda b: b.group)
    keybindings_surface = pg.Surface(
        (screen.get_width() // 2, screen.get_height() // 2)
    )
    keybindings_surface.fill(black)
    keybindings_rect = keybindings_surface.get_rect()
    keybindings_rect.x, keybindings_rect.y = rect_screen_center(
        keybindings_rect, center_x=True, center_y=True
    )

    binding_text_position = pg.Rect((line_width + 10, 0), (0, 0))
    for group, bindings in grouped_bindings:
        text = f"{group}: {', '.join([pg.key.name(binding.keycode) for binding in bindings])}"
        text_surface = new_text_surface(text, color=white)
        binding_text_position.move_ip(0, text_surface.get_height() + 10)
        keybindings_surface.blit(text_surface, binding_text_position)

    pg.draw.rect(
        keybindings_surface,
        white,
        pg.Rect((0, 0), (keybindings_rect.w, keybindings_rect.h)),
        width=line_width,
    )
    screen.blit(keybindings_surface, keybindings_rect)


def draw_help_keybind(help_binding: KeyBinding, rectangle_rect: pg.Rect):
    binding_text_position = rectangle_rect.move(0, (rectangle_rect.h + 20))
    text = f"{help_binding.group}: {pg.key.name(help_binding.keycode)}"
    text_surface = new_text_surface(text, color=white)
    text_rect = rect_screen_center(binding_text_position, center_x=True)
    binding_text_position.move_ip(0, text_surface.get_height() + 10)
    blit_text_to_screen(text_surface, text_rect)


def new_text_surface(text: str, size: int = 12, color: pg.color.Color = black):
    default_font = (
        Path(__file__).parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
    ).resolve()
    font = pygame.font.Font(default_font, size)
    return font.render(text, False, color, None)


def handle_input(keybindings: Iterable[KeyBinding]):
    on_pressed_bindings = set(filter(lambda k: k.on_pressed, keybindings))
    for binding in on_pressed_bindings:
        if pg.key.get_pressed()[binding.keycode]:
            binding.func()

    not_on_pressed_keybindings = set(keybindings).difference(on_pressed_bindings)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            sys.exit()

        for binding in not_on_pressed_keybindings:
            if event.type == pg.KEYDOWN and event.key == binding.keycode:
                binding.func()


def rect_screen_center(
    rect: pg.Rect, center_x=False, center_y=False
) -> Tuple[int, int]:
    screen = pygame.display.get_surface()
    rect = rect.copy()

    if center_x:
        rect.x = screen.get_rect().centerx - rect.w // 2

    if center_y:
        rect.y = screen.get_rect().centery - rect.h // 2

    return rect.x, rect.y


def resize_surface_by_percentage(surface: pg.Surface, percentage: int) -> pg.Surface:
    new_image_resolution = [
        xy * percentage // 100 for xy in (surface.get_width(), surface.get_height())
    ]
    return pg.transform.scale(surface, new_image_resolution)


def update_cursor_pos(**kwargs):
    args = (
        "resized_img_rect",
        "last_resized_img_rect",
        "original_image_rect",
        "cursor_rect",
        "zoom",
        "cursor_coords",
    )
    (
        resized_img_rect,
        last_resized_img_rect,
        original_image_rect,
        cursor_rect,
        zoom,
        cursor_coords,
    ) = (kwargs.get(arg) for arg in args)

    window_resized = last_resized_img_rect and last_resized_img_rect != resized_img_rect
    cursor_not_initialized = (cursor_rect.x, cursor_rect.y) == (0, 0)
    if cursor_not_initialized:
        cursor_rect.x, cursor_rect.y = resized_img_rect.x, resized_img_rect.y
        cursor_rect.w, cursor_rect.h = (
            resized_img_rect.w // original_image_rect.w,
            resized_img_rect.h // original_image_rect.h,
        )
    elif zoom["changed"] or window_resized:
        zoom["changed"] = False
        cursor_rect.x, cursor_rect.y = cursor_coords
        cursor_rect.w, cursor_rect.h = (
            resized_img_rect.w // original_image_rect.w,
            resized_img_rect.h // original_image_rect.h,
        )
        cursor_rect.x = cursor_rect.x * cursor_rect.w + resized_img_rect.x
        cursor_rect.y = cursor_rect.y * cursor_rect.h + resized_img_rect.y


def print_welcome_msg(func):
    def wrapper():
        click.clear()
        click.echo(
            click.style("pypixelart - A TOTALLY PRACTICAL IMAGE EDITOR", fg="red")
        )
        func()

    return wrapper


class PyPixelArt:
    def __init__(self, image: pg.Surface, path: pathlib.Path):
        self.image, self.path = image, path

        self.screen = pg.display.set_mode((600, 600), pg.RESIZABLE)
        self.app_name = click.get_current_context().command.name
        pg.display.set_caption(self.app_name)

        self.cursor_rect = pg.Rect((0, 0), (0, 0))
        self.cursor_draw_color = white

        self.resized_img_rect = self.last_resized_img_rect = None

        self.resized_img = self.rectangle_rect = None

        self.line_width = 4
        self.cursor_line_width = self.line_width // 2
        self.grid_line_width = 1
        self.symmetry_line_width = 4

        self.clock = pg.time.Clock()

        self.zoom = {
            "percent": 1000,
            "step": 100,
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
            "alpha": pg.Color(0, 0, 0, 0),
        }

        zoom_g, cursor_g = "Zoom", "Move Cursor"
        self.keybindings = [
            KeyBinding(pg.K_i, "Draw", lambda: self.draw_pixel(), on_pressed=True),
            KeyBinding(pg.K_u, "Undo", lambda: self.undo(), on_pressed=True),
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
        self.cursor_rect.move_ip(x * self.cursor_rect.w, y * self.cursor_rect.h)

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

    def cursor_coords_in_pixels(self) -> Tuple[int, int]:
        if not all((self.cursor_rect, self.last_resized_img_rect)):
            return 0, 0
        coord_x = (
            self.cursor_rect.x - self.last_resized_img_rect.x
        ) // self.cursor_rect.w
        coord_y = (
            self.cursor_rect.y - self.last_resized_img_rect.y
        ) // self.cursor_rect.h
        return coord_x, coord_y

    def draw_pixel(self):
        cursor_x, cursor_y = self.cursor_coords_in_pixels()
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

    def undo(self):
        if self.image_history:
            saved_img: pg.Surface = self.image_history.pop()
            self.image.fill((0, 0, 0, 0))
            self.image.blit(saved_img, (0, 0), saved_img.get_rect())

    def save(self):
        pg.image.save(self.image, self.path)
        click.echo(f"Saved {self.path}")

    def run_loop(self):

        while True:
            self.screen.fill(grey)

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

            update_cursor_pos(
                resized_img_rect=self.resized_img_rect,
                last_resized_img_rect=self.last_resized_img_rect,
                original_image_rect=self.image.get_rect(),
                cursor_rect=self.cursor_rect,
                zoom=self.zoom,
                cursor_coords=self.cursor_coords_in_pixels(),
            )

            if self.grid:
                where = self.resized_img.get_rect().move(
                    (self.resized_img_rect.x, self.resized_img_rect.y)
                )
                grid_rect_size = self.cursor_rect.w, self.cursor_rect.h
                draw_grid(where, grid_rect_size, self.grid_line_width)

            draw_symmetry_line(
                self.symmetry,
                self.resized_img.get_rect().move(
                    (self.resized_img_rect.x, self.resized_img_rect.y)
                ),
                self.symmetry_line_width,
            )

            cursor_image_color = black if self.grid else white
            pg.draw.rect(
                self.screen,
                cursor_image_color,
                self.cursor_rect,
                width=self.cursor_line_width,
            )

            cursor_coords_text_rect = draw_cursor_coordinates(
                self.cursor_coords_in_pixels(), self.rectangle_rect.topleft
            )

            rect_top_right_corner_x, _ = self.rectangle_rect.topright
            draw_selected_color(
                self.cursor_draw_color,
                rect_top_right_corner_x=rect_top_right_corner_x,
                cursor_coord_text_y=cursor_coords_text_rect.y,
            )

            previous_cursor_x, previous_cursor_y = (
                self.cursor_rect.x,
                self.cursor_rect.y,
            )

            handle_input(self.keybindings)

            if not self.resized_img_rect.colliderect(self.cursor_rect):
                self.cursor_rect.x, self.cursor_rect.y = (
                    previous_cursor_x,
                    previous_cursor_y,
                )

            if self.show_bindings:
                draw_keybindings(self.keybindings, self.line_width)
            else:
                draw_help_keybind(self.help_keybinding, self.rectangle_rect)

            if self.color_selection:
                draw_color_selection(self.palette_colors, self.line_width)

            pg.display.flip()

            self.clock.tick(60)


@print_welcome_msg
@click.command(name="pypixelart")
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
        img_size = list(
            map(int, resolution.split(","))
            if resolution
            else map(int, (input(f"Image {x}: ") for x in ("width", "height")))
        )
        image = pg.Surface(img_size, pygame.SRCALPHA)

    pypixelart = PyPixelArt(image, path)
    pypixelart.run_loop()


if __name__ == "__main__":
    main()
