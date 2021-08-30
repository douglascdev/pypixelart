# pypixelart: a keyboard-centered approach to pixel art

## Features
pypixelart has many exciting functionalities, including
- Editing pixels *one at a time*!
- Vim keybindings by default!
- A grid!

<img src="https://raw.githubusercontent.com/douglascdev/pypixelart/main/.github/images/grid.gif">

- Vertical and horizontal symmetry to draw the same pixel in two sides!

<img src="https://raw.githubusercontent.com/douglascdev/pypixelart/main/.github/images/symmetry.gif">

- Zoom !

<img src="https://raw.githubusercontent.com/douglascdev/pypixelart/main/.github/images/zoom.gif">

To do:
- Saving images!
- An undo function!
- A fill tool!
- Cool image filters!
- Color palette presets

## Installation

Install the package with:
```sh
pip install pypixelart
```

## Usage

Run with `pypixelart`.

You can also specify the file path and resolution: for example, to create a new image that is 20px wide and 10px tall you can use

```
pypixelart -f new_image.png -res 20,10
```
To get the full list of options:

```
$ pypixelart --help
Usage: pypixelart [OPTIONS]

Options:
  -f, --filepath PATH      Path for the file you want to open
  -res, --resolution TEXT  Image height and width separated by a comma, e.g.
                           20,10 for a 20x10 image. Note that no spaces can be
                           used.
  --help                   Show this message and exit.
```
