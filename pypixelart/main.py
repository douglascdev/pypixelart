import itertools
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


def resize_surface_by_percentage(surface: pg.Surface, percentage: int) -> pg.Surface:
    new_image_resolution = [
        xy * percentage // 100 for xy in (surface.get_width(), surface.get_height())
    ]
    return pg.transform.scale(surface, new_image_resolution)


def new_text_surface(text: str, size: int = 12, color: pg.color.Color = black):
    default_font = (
        Path(__file__).parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
    ).resolve()
    font = pygame.font.Font(default_font, size)
    return font.render(text, False, color, None)


def blit_text(
    draw: Union[str, pg.Surface], coord: Union[Iterable, Tuple[int, int], pg.Rect]
):
    surface = draw if isinstance(draw, pg.Surface) else new_text_surface(str(draw))
    pg.display.get_surface().blit(surface, coord)


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


def draw_welcome_msg(func):
    def wrapper():
        click.clear()
        click.echo(
            click.style("pypixelart - A TOTALLY PRACTICAL IMAGE EDITOR", fg="red")
        )
        func()

    return wrapper


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


@draw_welcome_msg
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

    screen = pg.display.set_mode((600, 600), pg.RESIZABLE)
    app_name = click.get_current_context().command.name
    pg.display.set_caption(app_name)

    cursor_rect = pg.Rect((0, 0), (0, 0))
    cursor_draw_color = {"color": white}

    img_screen_pos, last_img_screen_pos = None, None

    line_width = 4
    cursor_line_width = line_width // 2
    grid_line_width = 1
    symmetry_line_width = 4

    clock = pg.time.Clock()

    zoom = {
        "percent": 1000,
        "step": 100,
        "changed": False,
    }

    grid = {
        "on": False,
    }

    color_selection = {
        "on": False,
    }

    show_bindings = {
        "on": False,
    }
    show_bindings_obj = KeyBinding(pg.K_SPACE, "Help", lambda: set_show_bindings())

    pallete_colors = {
        "red": pg.Color(172, 50, 50),
        "cream": pg.Color(217, 160, 102),
        "brown": pg.Color(102, 57, 49),
        "black": pg.Color(0, 0, 0),
        "blue": pg.Color(91, 110, 225),
        "yellow": pg.Color(251, 242, 54),
        "alpha": pg.Color(0, 0, 0, 0),
    }

    image_history = list()

    symmetry = {"status": SymmetryType.NoSymmetry}

    def change_zoom(is_positive: bool):
        to_add = zoom["step"] if is_positive else -zoom["step"]
        if zoom["percent"] + to_add > 0:
            zoom["changed"] = True
            zoom["percent"] += to_add

    def move_cursor(x: int, y: int):
        cursor_rect.move_ip(x * cursor_rect.w, y * cursor_rect.h)

    def set_grid():
        grid["on"] = not grid["on"]

    def set_symmetry():
        symmetry["status"] = SymmetryType(
            (symmetry["status"].value + 1) % len(list(SymmetryType))
        )

    def set_color_selection():
        color_selection["on"] = not color_selection["on"]

    def set_show_bindings():
        show_bindings["on"] = not show_bindings["on"]

    def set_cursor_color(selected_color: pg.Color):
        color_selection["on"] = False
        cursor_draw_color["color"] = selected_color

    def cursor_coords_in_pixels() -> Tuple[int, int]:
        if not all((cursor_rect, last_img_screen_pos)):
            return 0, 0
        coord_x = (cursor_rect.x - last_img_screen_pos[0]) // cursor_rect.w
        coord_y = (cursor_rect.y - last_img_screen_pos[1]) // cursor_rect.h
        return coord_x, coord_y

    def draw_pixel():
        cursor_coords = list(cursor_coords_in_pixels())
        image_history.append(image.copy())
        image.set_at(cursor_coords, cursor_draw_color["color"])

        if symmetry["status"] != SymmetryType.NoSymmetry:
            middle_w, middle_h = image.get_width() // 2, image.get_height() // 2
            if symmetry["status"] == SymmetryType.Vertical:

                cursor_coords[0] = middle_w + (middle_w - cursor_coords[0]) - 1
                image.set_at(cursor_coords, cursor_draw_color["color"])
            elif symmetry["status"] == SymmetryType.Horizontal:

                cursor_coords[1] = middle_h + (middle_h - cursor_coords[1]) - 1
                image.set_at(cursor_coords, cursor_draw_color["color"])

    def undo():
        if image_history:
            saved_img: pg.Surface = image_history.pop()
            image.fill((0, 0, 0, 0))
            image.blit(saved_img, (0, 0), saved_img.get_rect())

    def save():
        pg.image.save(image, filepath)
        click.echo(f"Saved {filepath}")

    zoom_g, cursor_g = "Zoom", "Move Cursor"
    keybindings = [
        KeyBinding(pg.K_i, "Draw", lambda: draw_pixel(), on_pressed=True),
        KeyBinding(pg.K_u, "Undo", lambda: undo(), on_pressed=True),
        KeyBinding(pg.K_w, "Save file", lambda: save()),
        KeyBinding(pg.K_n, zoom_g, lambda: change_zoom(True), on_pressed=True),
        KeyBinding(pg.K_b, zoom_g, lambda: change_zoom(False), on_pressed=True),
        KeyBinding(pg.K_k, cursor_g, lambda: move_cursor(0, -1)),
        KeyBinding(pg.K_j, cursor_g, lambda: move_cursor(0, 1)),
        KeyBinding(pg.K_l, cursor_g, lambda: move_cursor(1, 0)),
        KeyBinding(pg.K_h, cursor_g, lambda: move_cursor(-1, 0)),
        KeyBinding(pg.K_g, "Grid", lambda: set_grid()),
        KeyBinding(pg.K_s, "Symmetry", lambda: set_symmetry()),
        KeyBinding(pg.K_ESCAPE, "Exit", lambda: sys.exit()),
        KeyBinding(pg.K_c, "Color selection", lambda: set_color_selection()),
    ]

    keybindings += [
        KeyBinding(
            pg.key.key_code(str(i)),
            "Color",
            lambda c=name_color[1]: set_cursor_color(c),
        )
        for i, name_color in enumerate(pallete_colors.items(), start=1)
    ]

    keybindings += [show_bindings_obj]

    while True:
        screen.fill(grey)

        # Draws header text
        header_text = f"{app_name}: {path.name} ({image.get_width()}x{image.get_height()}) {zoom['percent']}%"
        text_surface = new_text_surface(header_text, color=red)
        text_rect = rect_screen_center(
            text_surface.get_rect().move(0, 10), center_x=True
        )
        blit_text(text_surface, text_rect)

        # Draws the selected image
        resized_img = resize_surface_by_percentage(image, zoom["percent"])
        last_img_screen_pos = img_screen_pos
        img_screen_pos = rect_screen_center(
            resized_img.get_rect(), center_x=True, center_y=True
        )
        screen.blit(resized_img, img_screen_pos)

        # Draws the rectangle around the image
        rectangle_x, rectangle_y = (
            img_screen_pos[0] - line_width,
            img_screen_pos[1] - line_width,
        )
        rectangle_w, rectangle_h = (
            resized_img.get_rect().w + line_width,
            resized_img.get_rect().h + line_width,
        )
        rectangle_rect = pg.Rect((rectangle_x, rectangle_y), (rectangle_w, rectangle_h))
        pg.draw.rect(screen, white, rectangle_rect, width=line_width)

        # Initializes cursor values
        window_resized = last_img_screen_pos and last_img_screen_pos != img_screen_pos
        if (cursor_rect.x, cursor_rect.y) == (0, 0):
            cursor_rect.x, cursor_rect.y = img_screen_pos[0], img_screen_pos[1]
            cursor_rect.w, cursor_rect.h = (
                resized_img.get_width() // image.get_width(),
                resized_img.get_height() // image.get_height(),
            )
        elif zoom["changed"] or window_resized:
            zoom["changed"] = False
            cursor_rect.x, cursor_rect.y = cursor_coords_in_pixels()
            cursor_rect.w, cursor_rect.h = (
                resized_img.get_width() // image.get_width(),
                resized_img.get_height() // image.get_height(),
            )
            cursor_rect.x = cursor_rect.x * cursor_rect.w + img_screen_pos[0]
            cursor_rect.y = cursor_rect.y * cursor_rect.h + img_screen_pos[1]

        # Draws a grid of rectangles around each pixel
        if grid["on"]:
            where = resized_img.get_rect().move(img_screen_pos)
            grid_rect_size = cursor_rect.w, cursor_rect.h
            draw_grid(where, grid_rect_size, grid_line_width)

        # Draws a line indicating where symmetry starts
        draw_symmetry_line(
            symmetry["status"],
            resized_img.get_rect().move(img_screen_pos),
            symmetry_line_width,
        )

        # Draws the rectangle that corresponds to the cursor
        cursor_image_color = black if grid["on"] else white
        pg.draw.rect(screen, cursor_image_color, cursor_rect, width=cursor_line_width)

        # Draws cursor coordinates above the rectangle
        cursor_coords_text_pos = list(rectangle_rect.topleft)
        cursor_pixels_x, cursor_pixels_y = cursor_coords_in_pixels()
        text = f"({cursor_pixels_x}, {cursor_pixels_y})"
        text_surface = new_text_surface(text, color=white)
        cursor_coords_text_pos[1] -= 20
        blit_text(text_surface, cursor_coords_text_pos)

        # Draws selected color
        draw_selected_color(
            cursor_draw_color["color"],
            rect_top_right_corner_x=rectangle_rect.topright[0],
            cursor_coord_text_y=cursor_coords_text_pos[1],
        )

        cursor_rect_backup = cursor_rect.x, cursor_rect.y

        handle_input(keybindings)

        # Restore position from before input if the cursor is outside the rectangle
        img_rect_pos = resized_img.get_rect().move(img_screen_pos)
        if not img_rect_pos.colliderect(cursor_rect):
            cursor_rect.x, cursor_rect.y = cursor_rect_backup

        # Draws keybindings on screen
        if show_bindings["on"]:
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
        else:
            binding_text_position = rectangle_rect.move(0, (rectangle_h + 20))
            text = (
                f"{show_bindings_obj.group}: {pg.key.name(show_bindings_obj.keycode)}"
            )
            text_surface = new_text_surface(text, color=white)
            text_rect = rect_screen_center(binding_text_position, center_x=True)
            binding_text_position.move_ip(0, text_surface.get_height() + 10)
            blit_text(text_surface, text_rect)

        # Color selection
        if color_selection["on"]:
            palette_rect = pg.Rect(
                (0, 0), (screen.get_width() // 2, screen.get_height() // 2)
            )
            palette_surface = pg.Surface((palette_rect.w, palette_rect.h))
            palette_surface.fill(black)

            for i, name_color in enumerate(pallete_colors.items(), start=1):
                name, color = name_color
                color_surface = pg.Surface((palette_rect.w // 10, palette_rect.h // 10))
                pg.draw.rect(color_surface, color, color_surface.get_rect())
                color_binding_text = new_text_surface(str(i), color=~color)
                center_x = (
                    color_surface.get_rect().center[0]
                    - color_binding_text.get_width() // 2
                )
                center_y = (
                    color_surface.get_rect().center[1]
                    - color_binding_text.get_height() // 2
                )
                color_surface.blit(color_binding_text, (center_x, center_y))
                palette_surface.blit(
                    color_surface, ((i - 1) * color_surface.get_width(), 0)
                )

            pg.draw.rect(palette_surface, white, palette_rect, width=line_width)
            palette_rect.x, palette_rect.y = rect_screen_center(
                palette_rect, center_x=True, center_y=True
            )
            screen.blit(palette_surface, palette_rect)

            # Draws color selection title
            cursor_coords_text_pos = list(palette_rect.midtop)
            text = f"Color selection"
            text_surface = new_text_surface(text, color=white)
            cursor_coords_text_pos[0] -= text_surface.get_width() // 2
            cursor_coords_text_pos[1] -= 20
            blit_text(text_surface, cursor_coords_text_pos)

        pg.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()
