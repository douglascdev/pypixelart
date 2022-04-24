# PyPixelArt - A keyboard-centric pixel editor

![amogus_pixelart](https://user-images.githubusercontent.com/38195951/164997677-c68e59b1-714b-47e9-9f07-f01f689a5578.gif)
![pypixelart-compressed](https://user-images.githubusercontent.com/38195951/131579379-96c7e154-b8d4-4800-863e-4f1d541d1764.gif)

The idea behind PyPixelArt is uniting:
 - a [cmdpxl](https://github.com/knosmos/cmdpxl) inspired pixel image editor applied to pixel art.
 - [vim](https://github.com/vim/vim) 's keyboard-centric approach to improve productivity. Pretty hard to do with an image editor, but it'll be fun to try xD
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
PyPixelArt - A keyboard-centric pixel editor
Usage: pypixelart [OPTIONS]

Options:
  -f, --filepath PATH      Path for the file you want to open
  -res, --resolution TEXT  Image height and width separated by a comma, e.g.
                           20,10 for a 20x10 image. Note that no spaces can be
                           used.
  --debug                  Print debug-level logging to standard output
  --help                   Show this message and exit.
```

## Contribute!

Any contributions and forks and welcomed and encouraged!

Here's how you can contribute:
 - Fork the repository
 - Mess around with the code and use [black](https://pypi.org/project/black/) to format it
 - Submit a [Pull Request](https://github.com/douglascdev/pypixelart/pulls).
