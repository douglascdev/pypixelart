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
    """
    Blit an existing text surface or create a new text surface for a text and blit
    it to pygame's display surface at the specified coordinate
    """
    surface = draw if isinstance(draw, pg.Surface) else new_text_surface(str(draw))
    pg.display.get_surface().blit(surface, coord)


def draw_selected_color(
    color: pg.Color, rect_top_right_corner_x: int, cursor_coord_text_y: int
):
    """
    Draw in pygame's display surface what is the currently selected color by the user
    """
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
    """
    Draw in pygame's display surface a window showing all the colors available in the palette
    and each of their corresponding keybindings
    """
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


def draw_scaled_image(image: pg.Surface, percent: int) -> Tuple[pg.Surface, pg.Rect]:
    """
    Draw in pygame's display surface the image scaled to the specified percentage.
    Return the scaled surface and it's Rect object.
    """
    scaled_img = scale_surface(image, percent)
    scaled_img_rect = pg.Rect(
        rect_screen_center(scaled_img.get_rect(), center_x=True, center_y=True),
        (scaled_img.get_width(), scaled_img.get_height()),
    )
    pg.display.get_surface().blit(scaled_img, scaled_img_rect)
    return scaled_img, scaled_img_rect


def draw_symmetry_line(sym_type: SymmetryType, rect: pg.Rect, line_width: int):
    """
    Draw in pygame's display surface a line separating the middle of the image
    vertically or horizontally depending on the symmetry type, to indicate to
    the user how the symmetry is getting applied.
    """
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
    """
    Draw in pygame's display surface a grid around the pixels of the image
    """
    rectangles_w, rectangles_h = size
    surface = pg.display.get_surface()
    for i in range(where.y + rectangles_h, where.y + where.h, rectangles_h):
        pg.draw.line(surface, WHITE, (where.x, i), (where.x + where.w - line_width, i))
    for j in range(where.x + rectangles_w, where.x + where.w, rectangles_w):
        pg.draw.line(surface, WHITE, (j, where.y), (j, where.y + where.h - line_width))


def draw_header_text(**kwargs):
    """
    Draw in pygame's display surface the header text with the name of the app,
    the path of the image getting edited, width and height of the image and
    the current zoom
    """
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
    """
    Draw in pygame's display surface the rectangle displays a border around the image
    """
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
    """
    Draw in pygame's display surface the coordinates where the cursor is at in the image
    """
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


def draw_keybindings(keybindings: Iterable[KeyBinding], line_width: int) -> None:
    """
    Draw in pygame's display surface all the available keybindings
    """
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


def draw_help_keybind(help_binding: KeyBinding, rectangle_rect: pg.Rect) -> None:
    """
    Draw in pygame's display surface what keybind the user has to press to show
    all the other available keybindings
    """
    binding_text_position = rectangle_rect.move(0, (rectangle_rect.h + 20))
    text = f"{help_binding.group}: {pg.key.name(help_binding.keycode)}"
    text_surface = new_text_surface(text, color=WHITE)
    text_rect = rect_screen_center(binding_text_position, center_x=True)
    binding_text_position.move_ip(0, text_surface.get_height() + 10)
    blit_text_to_screen(text_surface, text_rect)


def new_text_surface(
    text: str, size: int = 12, color: pg.color.Color = BLACK
) -> pg.Surface:
    """
    Return a pygame Surface with the rendering of the text using the specified size and the default font.
    """
    default_font = (
        Path(__file__).parent / "assets" / "fonts" / "PressStart2P-Regular.ttf"
    ).resolve()
    font = pg.font.Font(default_font, size)
    return font.render(text, False, color, None)


def rect_screen_center(
    rect: pg.Rect, center_x=False, center_y=False
) -> Tuple[int, int]:
    """
    Return tuple of positions that centralize the rect in the middle of pygame's display surface
    for the x-axis, the y-axis or both.
    """
    screen = pg.display.get_surface()
    rect = rect.copy()

    if center_x:
        rect.x = screen.get_rect().centerx - rect.w // 2

    if center_y:
        rect.y = screen.get_rect().centery - rect.h // 2

    return rect.x, rect.y


def scale_surface(surface: pg.Surface, percentage: int) -> pg.Surface:
    """
    Scale surface to a specified percentage of it
    """
    new_image_resolution = [
        xy * percentage // 100 for xy in (surface.get_width(), surface.get_height())
    ]
    return pg.transform.scale(surface, new_image_resolution)


def draw_pixel(
    image: pg.Surface,
    position: Tuple[int, int],
    color: pg.Color,
    symmetry_type: SymmetryType,
) -> Union[None, Tuple[Tuple[int, int], pg.Color]]:
    """
    Draw a pixel of the selected color at the determined position of image, taking symmetry type
    into account to determine whether to and how to mirror the change done in position to its
    symmetric pixel, horizontally or vertically.

    For a coordinate (x, y) and an image of width and height (w, h) and considering
    d is the difference between the middle width w / 2 and x, the coordinate for the
    vertically symmetric pixel of (x, y) is (w / 2 + d, y), mirroring the pixel.

    For a coordinate (x, y) and an image of width and height (w, h) and considering
    d is the difference between middle height h / 2 and y, the coordinate for the
    horizontally symmetric pixel of (x, y) is (x, h / 2 + d), mirroring the pixel.

    In addition, integer division is used in the code to divide the height and width
    to avoid getting float values when dividing odd values, and 1 has to be subtracted
    to account for 0-indexing.

    Return None if no symmetry is set.
    Return position and color of symmetric pixel if SymmetryType is not NoSymmetry.
    """
    pixel_x, pixel_y = position

    if symmetry_type is SymmetryType.NoSymmetry:
        image.set_at(position, color)
        return None

    elif symmetry_type is SymmetryType.Vertical:
        image.set_at(position, color)
        middle_w = image.get_width() // 2
        symmetric_draw_pos = (middle_w + (middle_w - pixel_x) - 1, pixel_y)
        symmetric_pos_color = image.get_at(symmetric_draw_pos)
        image.set_at(symmetric_draw_pos, color)
        return symmetric_draw_pos, symmetric_pos_color

    elif symmetry_type is SymmetryType.Horizontal:
        image.set_at(position, color)
        middle_h = image.get_height() // 2
        symmetric_draw_pos = (pixel_x, middle_h + (middle_h - pixel_y) - 1)
        symmetric_pos_color = image.get_at(symmetric_draw_pos)
        image.set_at(symmetric_draw_pos, color)
        return symmetric_draw_pos, symmetric_pos_color
