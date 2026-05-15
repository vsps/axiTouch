<pre>
    :::     :::    ::: ::::::::::: ::::::::::: ::::::::  :::    :::  ::::::::  :::    ::: 
  :+: :+:   :+:    :+:     :+:         :+:    :+:    :+: :+:    :+: :+:    :+: :+:    :+: 
 +:+   +:+   +:+  +:+      +:+         +:+    +:+    +:+ +:+    +:+ +:+        +:+    +:+ 
+#++:++#++:   +#++:+       +#+         +#+    +#+    +:+ +#+    +:+ +#+        +#++:++#++ 
+#+     +#+  +#+  +#+      +#+         +#+    +#+    +#+ +#+    +#+ +#+        +#+    +#+ 
#+#     #+# #+#    #+#     #+#         #+#    #+#    #+# #+#    #+# #+#    #+# #+#    #+# 
###     ### ###    ### ###########     ###     ########   ########   ########  ###    ### 
</pre>


## AXITOUCH

AxiTouch is a Touchdesigner setup that lets you drive an AxiDraw plotter "directly" from Touch.
Currently it saves an SVG and sends it to the plotter so it might not qualify as actually directly driving it but it's a start. I may look into full, realtime interactive mode.
Let me know if it works on other hardware.

Interrupting a plot is a little unpredictable.

Entirely vibe coded so good luck everybody!

---

## Installation

You need to install the python library found here:
<code>
python -m pip install https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip
</code>

AxiDraw docs: [AxiDraw py api docs](https://axidraw.com/doc/py_api/#introduction)

I have tried tested it on the AxiDraw SE/A1. Runs smoothly on quite large SVG files.

The sinSpin.toc is already set up - you can tweak parameters in the base component.
Check the callback DAT for the SVG output location (this will be parameterised soon)

---

## Building your own — Quick Setup

### 1. Install pyaxidraw into TD's Python

Open TD Textport (Alt+T):
pythonimport subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install',
    'https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip'],
    capture_output=True, text=True)
Restart TD. If it installs to user site-packages, add a project-level Execute DAT firing on Start:
pythondef onStart():
    import sys
    path = r'C:\Users\piotr\AppData\Roaming\Python\python311\site-packages'
    if path not in sys.path:
        sys.path.append(path)
        
### 2. Base COMP structure

Inside base1 create:

axidraw_ext — Text DAT, paste axidraw_ext.py
status — Text DAT (empty, extension writes here)
chopexec1 — CHOP Execute DAT, paste callbacks code, point CHOP at /project1/base1/container1/out1, enable Off to On

On base1 Extensions page:

Object: op('axidraw_ext') — Name: AxiDrawExt — Promote: On

Custom parameters on base1 (AxiDraw page):

| Name | Type | Default |
|------|------|---------|
|Port|Str|COM4|
|Model|StrMenu|A4,A3,A2,A1|
|Paper|StrMenu|A4,A3,A2,A1|
|Speedpendown|Int|25|
|Speedpenup|Int|75|
|Penposdown|Int|40|
|Penposup|Int|60|

### 3. Panel buttons

Inside container1, create Momentary buttons named:
connect, disconnect, pen_up, pen_down, motors_off, home, save_svg, plot, pause, stop
Merge all into a Merge CHOP → Out CHOP.

### 4. Find your COM port

pythonimport serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(port.device, port.description)
EiBotBoard (UBW-based) = your AxiDraw. Set that port on base1.

### 5. Workflow

Hit Connect — status DAT shows connected
Hit Motors Off to release carriage and set home position manually
Hit Connect again to re-engage
Hit Save SVG to capture current CHOP data
Hit Plot to send to plotter
Hit Stop to cancel (raises pen)
