# Run this ONCE in the TouchDesigner Textport (Alt+T) to install pyaxidraw
# into TD's bundled Python environment.
#
# TD 2025.x bundles Python 3.11 — pyaxidraw supports 3.8+, so this works.

import subprocess
import sys

print("TD Python:", sys.executable)
print("Installing pyaxidraw...")

result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install',
     'https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip'],
    capture_output=True, text=True
)

print(result.stdout)
if result.returncode != 0:
    print("ERRORS:", result.stderr)
else:
    print("Done. Restart TD to pick up the new package.")

# Verify:
try:
    from pyaxidraw import axidraw
    print("pyaxidraw import OK")
except ImportError as e:
    print("Import failed:", e)
