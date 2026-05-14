# callbacks.py
# Put this in a Script DAT or an Execute DAT wired to your panel buttons.
# Each function name matches a button name in the Control Panel COMP.
#
# Assumes this DAT lives inside the same base COMP as the extension.
# Access the ext via: parent().ext.AxiDrawExt

def onOffToOn(channel, sampleIndex, val, prev):
    name = channel.name
    ext  = parent().ext.AxiDrawExt

    if name == 'connect':
        ext.Connect()

    elif name == 'disconnect':
        ext.Disconnect()

    elif name == 'pen_up':
        ext.PenUp()

    elif name == 'pen_down':
        ext.PenDown()

    elif name == 'motors_off':
        ext.DisengageMotors()

    elif name == 'home':
        ext.Home()

    elif name == 'save_svg':
        xy = op('/project1/OUT')
        
        xs = list(xy['x'].vals)
        ys = list(xy['y'].vals)
        
        # Downsample — keep every Nth point
        step = 1  # increase if still jittery
        xs = xs[::step]
        ys = ys[::step]

        #w, h   = 594, 420
        w, h   = 420, 297  # A3 landscape mm
        margin = 20
        # Use square drawing area based on shorter dimension
        draw_size = h - margin * 2  # 380mm square
        offset_x  = (w - draw_size) / 2  # centre horizontally

        def to_page_x(v):
            return offset_x + (v + 1) / 2 * draw_size

        def to_page_y(v):
            return margin + (1 - (v + 1) / 2) * draw_size
        
        points = ' '.join(
            f'{to_page_x(x):.4f},{to_page_y(y):.4f}'
            for x, y in zip(xs, ys)
        )
        
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{w}mm" height="{h}mm"
     viewBox="0 0 {w} {h}">
  <polyline points="{points}"
            fill="none" stroke="black" stroke-width="0.5"/>
</svg>'''
        
        import os
        path = r'Z:\WORK\PROJECTS\TOUCH_PROJECTS\sinSpin\plots\output.svg'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(svg)
        
        debug('SVG written: ' + path)



    elif channel.name == 'plot':
        path = r'Z:\WORK\PROJECTS\TOUCH_PROJECTS\sinSpin\plots\output.svg'
        if not __import__('os').path.exists(path):
            debug('No SVG saved yet — hit save_svg first')
            return
        ext.PlotSVG(path)


    elif name == 'pause':
        if ext.IsPlotting:
            ext.PausePlot()
        else:
            ext.ResumePlot()

    elif name == 'stop':
        ext.StopPlot()


def onValueChange(channel, sampleIndex, val, prev):
    pass
