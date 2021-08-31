# pypixelart: a keyboard-centered approach to pixel art

![pypixelart-compressed](https://user-images.githubusercontent.com/38195951/131579379-96c7e154-b8d4-4800-863e-4f1d541d1764.gif)

The idea behind pypixelart is uniting:
 - a [cmdpxl](https://github.com/knosmos/cmdpxl) inspired pixel image editor applied to pixel art.
 - [vim](https://github.com/vim/vim) 's keyboard-centered approach to improve productivity. Pretty hard to do with an image editor, but we'll try.
 - Some very useful functionalities from [aseprite](https://github.com/aseprite/aseprite) and other pixel art editors, such as screen symmetry.

## Features
pypixelart has many exciting functionalities, including
- Editing pixels *one at a time*!
- Saving images!
- An undo function!
- Vim keybindings by default!
- A grid!

![grid](https://user-images.githubusercontent.com/38195951/131271151-3093ee75-ef13-4c6c-9391-73519b19b572.gif)

- Vertical and horizontal symmetry to draw the same pixel in two sides!

![symmetry](https://user-images.githubusercontent.com/38195951/131271153-93a452fa-ca09-4a43-b62f-decb9c8d9899.gif)

- Zoom !

![zoom](https://user-images.githubusercontent.com/38195951/131271152-319d9213-5753-49b2-a5c5-241e39153c02.gif)


To do:
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
