import sys
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Callable, Set, Tuple, Dict

import click
from PyQt6.QtGui import QImage, QPixmap, QKeySequence, QShortcut, QColor
from PyQt6.QtWidgets import QApplication, QLineEdit, QLabel, QStatusBar, QMainWindow
from PyQt6 import uic

from pypixelart.constants import QT_UI_PATH, COMMAND_PREFIX
from pypixelart.point import Point

""" 
Indicate whether the code is running as an application, showing 
the main window and all the Qt user interface elements or act like
a library executing methods in a supplied image.
"""
IS_RUNNING_AS_APPLICATION: bool = __name__ == "__main__"


def run_if_application(function):
    """
    Decorator for methods that should only run when the code
    is running as an application, mostly the ones relating to
    Ui stuff.
    """
    def wrapper(*args):
        if IS_RUNNING_AS_APPLICATION:
            function(*args)

    return wrapper


def command(command_dict: Dict[str, Callable], *command_aliases):
    """
    Decorator that inserts methods as commands
    """

    def wrapper(function):
        for alias in command_aliases:
            command_dict[f"{COMMAND_PREFIX}{alias}"] = function

    return wrapper


@dataclass
class Zoom:
    percent: int
    percent_change_step: int
    changed: int


@dataclass
class Overlay:
    overlay_image: QImage
    is_drawing_color_selection: bool
    is_drawing_grid: bool
    is_drawing_help: bool


@dataclass
class Cursor:
    position = Point(0, 0)
    color = QColor("white")


class PyPixelArt:

    image: QImage
    image_path: Path
    image_resized_preview: QLabel
    command_input: QLineEdit
    command_output: QStatusBar
    command_to_function_map: Dict[str, Callable] = dict()
    cursor: Cursor
    main_window: QMainWindow
    overlay: Overlay
    zoom: Zoom

    def __init__(self, image_path: Path, image: QImage):
        # General initializations, always executed
        self._initialize_image_attributes(image_path, image)
        self._initialize_cursor()

        # Methods only executed when running as application
        self._initialize_qt_window_ui()
        self._initialize_overlay_variables()
        self._initialize_shortcuts()
        self._initialize_zoom()

        self._update_window_title()
        self._update_image_preview()

        self._show_main_window()

    def _initialize_image_attributes(self, image_path: Path, image: QImage):
        """
        Initialize attributes to hold the values of the image and image_path
        passed as argument to the class constructor.

        The QImage class is used because of its capabilities for direct pixel
        access and manipulation
        """
        self.image_path: Path = image_path
        self.image: QImage = image

    def _initialize_cursor(self):
        self.cursor = Cursor()

    @run_if_application
    def _initialize_qt_window_ui(self):
        """
        Load the Qt form file describing the elements contained in the application's
        window and initialize the attributes corresponding to each ui element
        """
        self.main_window: QMainWindow = QMainWindow()
        uic.loadUi(Path(QT_UI_PATH / "mainwindow.ui"), self.main_window)

        self.command_input = self.main_window.command_input
        self.command_output = self.main_window.command_output
        self.image_resized_preview = self.main_window.image_resized_preview

        """
        Hide the input field for commands and the output, as the field should only be drawn
        after the user presses a keyboard shortcut to show it and the visible value cannot
        be changed in the form's ui file.
        """
        self.command_input.setVisible(False)
        self.command_output.setVisible(False)

    @run_if_application
    def _initialize_overlay_variables(self):
        """
        Initialize the overlay variables. The overlay is an image where elements that are not
        supposed to be saved along with the image can be placed, then drawn over the actual
        image to achieve their desired purpose.

        That includes the grid, which shows the boundary between pixels, and the color
        selection, which shows the color palette and the corresponding keybinding for
        each color.
        """

        overlay_image: QImage = QImage(self.image.size(), self.image.format())
        overlay_image.fill(QColor("alpha"))

        self.overlay = Overlay(
            overlay_image=overlay_image,
            is_drawing_grid=False,
            is_drawing_color_selection=False,
            is_drawing_help=False,
        )

    # def _draw_polygon(self):
    #     self.image.paintEngine().drawPolygon()

    @run_if_application
    def _initialize_shortcuts(self):
        # Shortcuts to open the command input
        QShortcut(QKeySequence("escape"), self.main_window, self._toggle_command_input)
        QShortcut(QKeySequence("ctrl+c"), self.main_window, self._toggle_command_input)
        QShortcut(
            QKeySequence(COMMAND_PREFIX), self.main_window, self._toggle_command_input_add_prefix
        )

        # Command input shortcuts to execute the command
        QShortcut(
            QKeySequence("return"), self.command_input, self._execute_input_command
        )
        QShortcut(
            QKeySequence("enter"), self.command_input, self._execute_input_command
        )

    @run_if_application
    def _initialize_zoom(self):

        image = self.image
        window_width, window_height = self.main_window.width(), self.main_window.height()

        """
        Get the biggest image dimension and take the inverse rule of
        three between the corresponding window dimension, 100 and the
        image dimension to get the appropriate zoom that keeps the
        image in the screen
        """
        if image.width() > image.height():
            logging.debug(
                f"Image width {image.width()} > image height {image.height()}"
            )
            initial_zoom_percent = (window_width * 100) // image.width()
            logging.debug(f"Zoom initialized to {initial_zoom_percent}")
        else:
            logging.debug(
                f"Image width {image.width()} <= image height {image.height()}"
            )
            initial_zoom_percent = (window_height * 100) // image.height()
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

        self.zoom = Zoom(
            percent=initial_zoom_percent,
            percent_change_step=zoom_step_percent,
            changed=False,
        )

    @run_if_application
    def _update_window_title(self):
        app_name = click.get_current_context().command.name
        filename = self.image_path.name
        image_width, image_height = self.image.width(), self.image.height()
        self.main_window.setWindowTitle(
            f"{app_name}: {filename} ({image_width}x{image_height}) {self.zoom.percent}%"
        )

    @run_if_application
    def _update_image_preview(self):
        self.image_resized_preview.setPixmap(QPixmap.fromImage(self.image))

    @run_if_application
    def _execute_input_command(self):
        command_text = self.command_input.text()

        if not command_text:
            logging.info("Tried to execute nothing as a command input")
            self.command_output.showMessage("Command not found.")
            self.command_output.setVisible(True)
            return

        command_name, *command_args = command_text.split()

        if command_name in self.command_to_function_map:
            logging.info(f"Command {command_name} found, now executing.")

            if command_args:
                result = self.command_to_function_map[command_name](self, command_args)
            else:
                result = self.command_to_function_map[command_name](self)

            logging.debug(f"Command result: \"{result}\"")

            self.command_output.setVisible(True)
            self.command_output.showMessage(result)
        else:
            logging.info(
                f"Command {command_name} was not found, showing error output."
            )
            self.command_output.showMessage("Command not found.")
            self.command_output.setVisible(True)

        self._toggle_command_input()

    @run_if_application
    def _show_main_window(self):
        self.main_window.show()

    @run_if_application
    def _toggle_command_input(self):
        self.command_input.setVisible(not self.command_input.isVisible())

        if self.command_input.isVisible():
            self.command_output.setVisible(False)
            logging.info(
                f"Command input set to visible, clearing text and focusing on it"
            )
            self.command_input.clear()
            self.command_input.setFocus()
        else:
            logging.info(f"Command input set to invisible, focusing on window")
            self.main_window.setFocus()

    @run_if_application
    def _toggle_command_input_add_prefix(self):
        logging.info("Toggling command input and adding prefix")
        self._toggle_command_input()
        self.command_input.setText(COMMAND_PREFIX)

    @run_if_application
    @command(command_to_function_map, "grid")
    def _toggle_grid_overlay(self):
        self.overlay.is_drawing_grid = not self.overlay.is_drawing_grid
        logging.info("Toggled grid")

    @command(command_to_function_map, "q")
    def _quit(self):
        sys.exit()

    @command(command_to_function_map, "w")
    def _save_image(self) -> str:
        logging.debug(f"Saving image: \"{self.image_path}\"")

        try:
            image_path_str = str(self.image_path)
            self.image.save(image_path_str)
            return f"Image successfully saved to \"{image_path_str}\"."

        except Exception as exception:
            logging.exception(exception)
            return "An error occurred when trying to save the file."

    @command(command_to_function_map, "c")
    def _set_cursor_color(self, color=None) -> str:
        logging.info(f"Setting cursor color")

        try:
            # Color is passed as a list, so get the first element as color
            color = next(iter(color))
        except Exception:
            # If there are no arguments, just show the current color
            return f"Current color is \"{self.cursor.color.name()}\"."

        try:
            self.cursor.color = QColor(color)

            if not self.cursor.color.isValid():
                raise Exception(f"Invalid color \"{self.cursor.color}\"")

            return f"Color successfully set to \"{color}\""
        except Exception as exception:
            logging.exception(exception)
            return f"Failed to set color to \"{color}\""


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

    path = Path(filepath)

    if path.exists() and path.is_file():
        logging.info(f"Path '{path}' exists and is file. Now loading as image.")
        image = QImage(str(path))
    else:
        logging.info("No valid path was provided, creating new surface.")

        if resolution:
            width, height = tuple(map(int, resolution.split(",")))
            img_size = width, height
            logging.info(f"Resolution {img_size} loaded from click argument")
        else:
            width = int(input("Image width: "))
            height = int(input("Image height: "))
            img_size = width, height
            logging.info(f"Resolution {img_size} loaded from input")

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(QColor("grey"))

    app = QApplication(sys.argv)
    main_window = PyPixelArt(path, image)
    sys.exit(app.exec())


if IS_RUNNING_AS_APPLICATION:
    main()
