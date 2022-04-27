import enum


class SymmetryType(enum.IntEnum):
    """
    Determines whether to and how to mirror changes done to the image.

    A more in-depth technical explanation of how the symmetric pixel
    is defined is available in the documentation for the draw_pixel
    function.

    The enum values are kept as manually assigned integers starting
    from 0 to ensure they work when used to calculate the next
    symmetry type, when the user presses the keybinding to change it.
    """

    # changes are not mirrored
    NoSymmetry = 0
    # changes are mirrored horizontally
    Horizontal = 1
    # changes are mirrored vertically
    Vertical = 2
