# callbacks.py
# Put this in a Script DAT or an Execute DAT wired to your panel buttons.
# Each function name matches a button name in the Control Panel COMP.
#
# Assumes this DAT lives inside the same base COMP as the extension.
# Access the ext via: parent().ext.AxiDrawExt


def onOffToOn(channel, sampleIndex, val, prev):
    name = channel.name
    ext = parent().ext.AxiDrawExt

    if name == "connect":
        ext.Connect()

    elif name == "disconnect":
        ext.Disconnect()

    elif name == "pen_up":
        ext.PenUp()

    elif name == "pen_down":
        ext.PenDown()

    elif name == "motors_off":
        ext.DisengageMotors()

    elif name == "home":
        ext.Home()

    elif name == "save_svg":
        xy = op("/project1/OUT")

        xs = list(xy["x"].vals)
        ys = list(xy["y"].vals)

        # Downsample — keep every Nth point
        step = 1  # increase if still jittery
        xs = xs[::step]
        ys = ys[::step]

        # Paper size lookup (landscape mm) — read from the COMP parameter
        PAPER_SIZES = {
            "A1": (841, 594),
            "A2": (594, 420),
            "A3": (420, 297),
            "A4": (297, 210),
        }
        paper = parent().par.Paper.eval() if parent().par.Paper is not None else "A3"
        w, h = PAPER_SIZES.get(paper, (420, 297))

        margin = 20
        # Use square drawing area based on shorter dimension
        draw_size = h - margin * 2
        offset_x = (w - draw_size) / 2  # centre horizontally

        def to_page_x(v):
            return offset_x + (v + 1) / 2 * draw_size

        def to_page_y(v):
            return margin + (1 - (v + 1) / 2) * draw_size

        points = " ".join(
            f"{to_page_x(x):.4f},{to_page_y(y):.4f}" for x, y in zip(xs, ys)
        )

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{w}mm" height="{h}mm"
     viewBox="0 0 {w} {h}">
  <polyline points="{points}"
            fill="none" stroke="black" stroke-width="0.5"/>
</svg>'''

        import os

        path = r"Z:\WORK\PROJECTS\TOUCH_PROJECTS\sinSpin\plots\output.svg"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(svg)

        debug("SVG written: " + path + "  (paper: " + paper + ")")

    elif channel.name == "plot":
        path = r"Z:\WORK\PROJECTS\TOUCH_PROJECTS\sinSpin\plots\output.svg"
        if not __import__("os").path.exists(path):
            debug("No SVG saved yet — hit save_svg first")
            return
        ext.PlotSVG(path)

    elif name == "pause":
        if ext.IsPlotting:
            ext.PausePlot()
        else:
            ext.ResumePlot()

    elif name == "stop":
        ext.StopPlot()


def onValueChange(channel, sampleIndex, val, prev):
    ext = parent().ext.AxiDrawExt
    name = channel.name

    if name in ("Penposdown", "Penposup"):
        pen_down = parent().par.Penposdown.eval()
        pen_up = parent().par.Penposup.eval()
        ext.SetPenPositions(pen_down, pen_up)
