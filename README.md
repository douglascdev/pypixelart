# PyPixelArt - A keyboard-centered pixel editor

![pypixelart-compressed](https://user-images.githubusercontent.com/38195951/131579379-96c7e154-b8d4-4800-863e-4f1d541d1764.gif)

The idea behind PyPixelArt is uniting:
 - a [cmdpxl](https://github.com/knosmos/cmdpxl) inspired pixel image editor applied to pixel art.
 - [vim](https://github.com/vim/vim) 's keyboard-centered approach to improve productivity. Pretty hard to do with an image editor, but we'll try.
 - Some very useful functionalities from [aseprite](https://github.com/aseprite/aseprite) and other pixel art editors, such as screen symmetry.

## Features and keybindings
- **Draw** : i
- **Erase**: x
- **Undo**: u
- **Save**: w
- **Zoom**: n, b
- **Move Cursor**: k, j, l, h
- **Grid**: g
- **Symmetry**: s
- **Color selection**: c
- **Color**: 1, 2, 3, 4, 5, 6
- **Help**: Space

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

## To do
- Add logging
- Add unit testing
- A fill tool
- Cool image filters
- Color palette presets
- A better way to switch between colors
- Allow editing colors on the color selection
