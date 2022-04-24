import itertools
import sys
from pathlib import Path
from typing import Union, Iterable, Tuple

import pygame as pg

from pypixelart.constants import *
from pypixelart.keybinding import KeyBinding
from pypixelart.symmetry_type import SymmetryType


def blit_text_to_screen(
    draw: Union[str, pg.Surface], coord: Union[Iterable, Tuple[int, int], pg.Rect]
):
    surface = draw if isinstance(draw, pg.Surface) else new_text_surface(str(draw))
    pg.display.get_surface().blit(surface, coord)


def draw_selected_color(
    color: pg.Color, rect_top_right_corner_x: int, cursor_coord_text_y: int
):
    selected_color_text = new_text_surface("Color: ", color=WHITE)
    w, h = selected_color_text.get_width(), selected_color_text.get_height()
    selected_color_surface = pg.Surface(
        (
            w + h,
            h,
        ),
        pg.SRCALPHA,
    )
    selected_color_surface.blit(selected_color_text, (0, 0))
    pg.draw.rect(
        selected_color_surface,
        color,
        pg.Rect(
            selected_color_text.get_rect().topright,
            (h, h),
        ),
        border_radius=DEFAULT_BORDER_RADIUS // 4,
    )
    pg.display.get_surface().blit(
        selected_color_surface,
        (
            rect_top_right_corner_x - w - h,
            cursor_coord_text_y,
        ),
    )


def draw_color_selection(palette_colors: dict, line_width: int):
    screen = pg.display.get_surface()
    palette_rect = pg.Rect((0, 0), (screen.get_width() // 2, screen.get_height() // 2))
    palette_surface = pg.Surface((palette_rect.w, palette_rect.h))
    palette_surface.fill(BLACK)

    for i, name_color in enumerate(palette_colors.items(), start=1):
        name, color = name_color
        color_surface = pg.Surface((palette_rect.w // 10, palette_rect.h // 10))
        color_surface_rect = color_surface.get_rect()
        (
            color_surface_center_x,
            color_surface_center_y,
        ) = color_surface_rect.center
        pg.draw.rect(
            color_surface,
            color,
            color_surface_rect,
            border_radius=DEFAULT_BORDER_RADIUS,
        )
        color_binding_text = new_text_surface(str(i), color=~color)
        center_x = color_surface_center_x - color_binding_text.get_width() // 2
        center_y = color_surface_center_y - color_binding_text.get_height() // 2
        color_surface.blit(color_binding_text, (center_x, center_y))
        palette_surface.blit(color_surface, ((i - 1) * color_surface_rect.w, 0))

    pg.draw.rect(
        palette_surface,
        WHITE,
        palette_rect,
        width=line_width,
        border_radius=DEFAULT_BORDER_RADIUS,
    )
    palette_rect.x, palette_rect.y = rect_screen_center(
        palette_rect, center_x=True, center_y=True
    )
    screen.blit(palette_surface, palette_rect)

    # Draws color selection title
    palette_mid_top_x, palette_mid_top_y = palette_rect.midtop
    selection_title_surface = new_text_surface("Color selection", color=WHITE)
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
        BLACK,
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
            WHITE,
            pg.Rect((i, j), (rectangles_w, rectangles_h)),
            width=line_width,
        )


def draw_header_text(**kwargs):
    app_name, path_name, width, height, zoom = (
        kwargs.get(arg) for arg in ("app_name", "path_name", "width", "height", "zoom")
    )
    header_text = f"{app_name}: {path_name} ({width}x{height}) {zoom}%"
    text_surface = new_text_surface(header_text, color=RED)
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
    pg.draw.rect(
        pg.display.get_surface(),
        WHITE,
        rectangle_rect,
        width=line_width,
        border_radius=DEFAULT_BORDER_RADIUS,
    )
    return rectangle_rect


def draw_cursor_coordinates(
    cursor_coords: Tuple[int, int], rectangle_top_left_coord: Tuple[int, int]
) -> pg.Rect:
    cursor_pixels_x, cursor_pixels_y = cursor_coords
    text = f"({cursor_pixels_x}, {cursor_pixels_y})"
    text_surface = new_text_surface(text, color=WHITE)
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
        (screen.get_width() // 2, screen.get_height() // 2), pg.SRCALPHA
    )

    keybindings_rect = keybindings_surface.get_rect()
    keybindings_rect.x, keybindings_rect.y = rect_screen_center(
        keybindings_rect, center_x=True, center_y=True
    )

    pg.draw.rect(
        keybindings_surface,
        BLACK,
        pg.Rect((0, 0), (keybindings_rect.w, keybindings_rect.h)),
        border_radius=DEFAULT_BORDER_RADIUS,
    )

    binding_text_position = pg.Rect((line_width + 10, 0), (0, 0))
    for group, bindings in grouped_bindings:
        text = f"{group}: {', '.join([pg.key.name(binding.keycode) for binding in bindings])}"
        text_surface = new_text_surface(text, color=WHITE)
        binding_text_position.move_ip(0, text_surface.get_height() + 10)
        keybindings_surface.blit(text_surface, binding_text_position)

    pg.draw.rect(
        keybindings_surface,
        WHITE,
        pg.Rect((0, 0), (keybindings_rect.w, keybindings_rect.h)),
        width=line_width,
        border_radius=DEFAULT_BORDER_RADIUS,
    )
    screen.blit(keybindings_surface, keybindings_rect)


def draw_help_keybind(help_binding: KeyBinding, rectangle_rect: pg.Rect):
    binding_text_position = rectangle_rect.move(0, (rectangle_rect.h + 20))
    text = f"{help_binding.group}: {pg.key.name(help_binding.keycode)}"
    text_surface = new_text_surface(text, color=WHITE)
    text_rect = rect_screen_center(binding_text_position, center_x=True)
    binding_text_position.move_ip(0, text_surface.get_height() + 10)
    blit_text_to_screen(text_surface, text_rect)


def new_text_surface(text: str, size: int = 12, color: pg.color.Color = BLACK):
    default_font = (
        Path(__file__).parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
    ).resolve()
    font = pg.font.Font(default_font, size)
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
    screen = pg.display.get_surface()
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
