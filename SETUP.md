# AxiDraw in TouchDesigner — Setup Guide
# TD 2025.32460 | pyaxidraw interactive + plot mode

## Step 1 — Install pyaxidraw into TD's Python

Open the TD Textport (Alt+T) and paste + run the contents of:
  install_pyaxidraw_in_td.py

Restart TouchDesigner after it completes.

---

## Step 2 — Build the base COMP

Create a Base COMP. Inside it, create these nodes:

### Text DATs
| Name         | Contents                        |
|--------------|---------------------------------|
| axidraw_ext  | paste axidraw_ext.py            |
| callbacks    | paste axidraw_callbacks.py      |
| svg_path     | (empty — user types path here)  |
| status       | (empty — extension writes here) |

### On the Base COMP itself
- Extensions page → add extension:
    Object: op('axidraw_ext')
    Name:   AxiDrawExt
    Promote: ON (so ext.AxiDrawExt works from outside)

### Custom Parameters on the Base COMP
Add these on a "AxiDraw" page (Extensions → Custom Parameters):

| Name         | Type    | Default | Range       |
|--------------|---------|---------|-------------|
| Port         | Str     | COM4    |             |
| Model        | StrMenu | A1      | A4,A3,A2,A1 |
| Paper        | StrMenu | A3      | A4,A3,A2,A1 |
| Speedpendown | Int     | 25      | 1-100       |
| Speedpenup   | Int     | 75      | 1-100       |
| Penposdown   | Int     | 40      | 0-100       |
| Penposup     | Int     | 60      | 0-100       |


---

## Step 3 — Wire up buttons

Create a Panel COMP (Container) with Momentary buttons named:
  connect, disconnect, pen_up, pen_down, motors_off, home, plot, pause, stop

Create a CHOP Execute DAT, set it to reference the panel's output CHOP.
Paste axidraw_callbacks.py into it.

The pause button toggles: if plotting → pause; if paused → resume.

---

## Step 4 — Set SVG path

Type or expression-link the SVG path into the `svg_path` Text DAT:
  C:/Users/piotr/plots/my_drawing.svg

Or drive it programmatically:
  op('base_axidraw/svg_path').clear()
  op('base_axidraw/svg_path').write('C:/path/to/file.svg')

---

## Step 5 — Using from elsewhere in your project

From any Python context in TD:

  ext = op('base_axidraw').ext.AxiDrawExt

  ext.Connect()
  ext.PenUp()
  ext.PenDown()
  ext.GoTo(50, 80)        # x, y in mm
  ext.MoveTo(0, 0)        # travel (pen up)
  ext.LineTo(100, 100)    # draw (pen down)
  ext.Home()
  ext.PlotSVG('C:/plots/test.svg')
  ext.PausePlot()
  ext.ResumePlot()
  ext.StopPlot()
  ext.Disconnect()

  print(ext.Status)        # 'disconnected' | 'connected' | 'plotting' | 'paused' | 'error'
  print(ext.ErrorMessage)

---

## Notes

### Threading
plot_run() blocks — it runs in a daemon thread so TD stays responsive.
PenUp/Down/GoTo etc. are synchronous but fast (USB serial roundtrip ~50ms).

### Pause/Resume during plot
pyaxidraw's plot mode doesn't natively support mid-plot pause via the Python API
(pause is EBB-level via button press). The current implementation stops the thread
cleanly and raises the pen. True pause/resume across sessions requires using
ad.options.mode = 'res_home' / 'res_plot' with the SVG output file — this is
an enhancement path if you need it.

### Units
Interactive mode defaults to mm (options.units = 2). Matches axiscope behaviour.

### Multiple AxiDraws
Set options.port = 'COM3' (or whatever port) before connecting if you have
more than one unit. You can read available ports with:
  from pyaxidraw import axidraw
  ad = axidraw.AxiDraw()
  ad.plot_setup()
  ad.options.mode = 'list'
  ad.plot_run()
