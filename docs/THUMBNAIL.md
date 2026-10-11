# Project thumbnail

`assets/qollab_thumbnail_wide.png` is pre-cropped to the very wide Qollab project-card ratio so the platform does not zoom into the center of a normal 16:9 image.

`visuals/thumbnail_manim.py` contains the Manim source used to build a simple project-card graphic.

Create a virtual environment and install Manim:

```bash
python3 -m venv .venv-manim
source .venv-manim/bin/activate
pip install --upgrade pip
pip install manim
```

Render the still frame:

```bash
manim -qh -s visuals/thumbnail_manim.py QScopeThumbnailFinal
```

Qollab displays project cards in a very wide crop. Keep important text and diagrams near the horizontal center and avoid placing essential content close to the top or bottom edges.
