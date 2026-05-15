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

## Building your own: SEE SETUP.md

