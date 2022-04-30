from pathlib import Path

# BLACK = pg.Color(20, 20, 20)
# WHITE = pg.Color(255, 255, 255)
# GREY = pg.Color(50, 50, 50)
# LIGHTER_GREY = pg.Color(80, 80, 80)
# RED = pg.Color(255, 80, 80)
# ALPHA = pg.Color(0, 0, 0, 0)

DEFAULT_BORDER_RADIUS = 8

PACKAGE_ROOT_PATH = Path(__file__).parent
PROJECT_ROOT_PATH = PACKAGE_ROOT_PATH.parent
QT_UI_PATH = PACKAGE_ROOT_PATH / "qt_forms"
COMMAND_PREFIX = ":"
