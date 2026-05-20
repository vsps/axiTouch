# axidraw_ext.py
# Drop into a Text DAT named 'axidraw_ext' inside your base COMP.
# Set the base COMP's extension to this class via the Extensions parameter.

import math
import threading

from pyaxidraw import axidraw

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
STATUS_DISCONNECTED = "disconnected"
STATUS_CONNECTED = "connected"
STATUS_PLOTTING = "plotting"
STATUS_PAUSED = "paused"
STATUS_ERROR = "error"


class AxiDrawExt:
    # Map human-readable paper sizes to AxiDraw API model codes
    # (see https://axidraw.com/doc/py_api/#model)
    _MODEL_MAP = {
        "A1": 5,  # AxiDraw SE/A1
        "A2": 6,  # AxiDraw SE/A2
        "A3": 2,  # AxiDraw V3/A3 or SE/A3
        "A4": 1,  # AxiDraw V2, V3, or SE/A4
    }

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self._comp_path = ownerComp.path  # capture path as plain string at init

        self._ad = None
        self._status = STATUS_DISCONNECTED
        self._error_msg = ""
        self._plot_thread = None
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

        self._points_done = 0
        self._points_total = 0

        self._pause_event.set()  # start unpaused

        self._tick_running = False
        self._update_status_dat()
        self._start_tick()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def Status(self):
        return self._status

    @property
    def IsConnected(self):
        return self._ad is not None and self._status != STATUS_DISCONNECTED

    @property
    def IsPlotting(self):
        return self._status == STATUS_PLOTTING

    @property
    def ErrorMessage(self):
        return self._error_msg

    @property
    def PointsDone(self):
        return self._points_done

    @property
    def PointsTotal(self):
        return self._points_total

    @property
    def PointsRemaining(self):
        return max(0, self._points_total - self._points_done)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def Connect(self):
        debug("spawning connect thread")
        opts = self._snapshot_options()
        t = threading.Thread(target=self._connect_worker, args=(opts,), daemon=True)
        t.start()
        debug("connect thread started, id: " + str(t.ident))

    def _connect_worker(self, opts):
        try:
            ad = axidraw.AxiDraw()
            ad.interactive()
            ad.options.units = 2
            ad.options.model = opts["model"]
            ad.options.speed_pendown = opts["speed_pendown"]
            ad.options.speed_penup = opts["speed_penup"]
            ad.options.pen_pos_down = opts["pen_pos_down"]
            ad.options.pen_pos_up = opts["pen_pos_up"]
            ad.options.accel = opts["accel"]
            if opts["port"]:
                ad.options.port = opts["port"]
            if not ad.connect():
                raise RuntimeError("AxiDraw connect() returned False — check USB")
            self._ad = ad
            self._set_status(STATUS_CONNECTED)
        except Exception as e:
            self._set_error(str(e))

    def Disconnect(self):
        t = threading.Thread(target=self._disconnect_worker, daemon=True)
        t.start()

    def _disconnect_worker(self):
        if self._ad is None:
            return
        try:
            self._ad.disconnect()
        except Exception:
            pass
        self._ad = None
        self._set_status(STATUS_DISCONNECTED)

    # ------------------------------------------------------------------
    # Motor / pen control (interactive mode)
    # ------------------------------------------------------------------

    def EngageMotors(self):
        pen = self._snapshot_pen()
        self._interactive_cmd(lambda ad: self._apply_pen_options(ad, pen) or ad.penup())

    def DisengageMotors(self):
        opts = self._snapshot_options()
        t = threading.Thread(target=self._disengage_worker, args=(opts,), daemon=True)
        t.start()

    def _disengage_worker(self, opts):
        # Close interactive session first
        if self._ad is not None:
            try:
                self._ad.disconnect()
            except Exception:
                pass
            self._ad = None

        try:
            ad = axidraw.AxiDraw()
            ad.plot_setup()
            ad.options.model = opts["model"]
            if opts["port"]:
                ad.options.port = opts["port"]
            ad.options.mode = "align"
            ad.plot_run()
        except Exception as e:
            self._set_error(str(e))
        finally:
            self._set_status(STATUS_DISCONNECTED)

    def PenUp(self):
        pen = self._snapshot_pen()
        self._interactive_cmd(lambda ad: self._apply_pen_options(ad, pen) or ad.penup())

    def PenDown(self):
        pen = self._snapshot_pen()
        self._interactive_cmd(lambda ad: self._apply_pen_options(ad, pen) or ad.pendown())

    def GoTo(self, x_mm, y_mm):
        self._interactive_cmd(lambda ad: ad.goto(x_mm, y_mm))

    def MoveTo(self, x_mm, y_mm):
        self._interactive_cmd(lambda ad: ad.moveto(x_mm, y_mm))

    def LineTo(self, x_mm, y_mm):
        self._interactive_cmd(lambda ad: ad.lineto(x_mm, y_mm))

    def Home(self):
        pen = self._snapshot_pen()
        self._interactive_cmd(
            lambda ad: (self._apply_pen_options(ad, pen), ad.penup(), ad.moveto(0, 0))
        )

    # ------------------------------------------------------------------
    # Plotting (interactive mode — streams polylines via draw_path)
    # ------------------------------------------------------------------

    def PlotPolylines(self, polylines):
        """Stream a list of polylines (each a list of [x_mm, y_mm]) to the EBB.

        Uses interactive draw_path so the firmware blends segments smoothly,
        matching the axiscope desktop plot path."""
        if self._status == STATUS_PLOTTING:
            debug("AxiDrawExt: already plotting — stop first")
            return
        if self._ad is None:
            debug("AxiDrawExt: not connected")
            return

        self._stop_event.clear()
        self._pause_event.set()
        try:
            self._ad.plot_status.stopped = 0
        except Exception:
            pass

        rs = self._snapshot_resample()
        polylines = self._resample_polylines(polylines, rs["min_seg"], rs["max_seg"])

        self._points_total = sum(len(p) for p in polylines if len(p) >= 2)
        self._points_done = 0
        self._set_status(STATUS_PLOTTING)

        pen = self._snapshot_pen()
        self._plot_thread = threading.Thread(
            target=self._plot_worker, args=(polylines, pen), daemon=True
        )
        self._plot_thread.start()

    def PlotSVG(self, svg_path):
        """Fallback SVG plot path (plot mode). Prefer PlotPolylines for smoothness."""
        if self._status == STATUS_PLOTTING:
            debug("AxiDrawExt: already plotting — stop first")
            return

        if self._ad is not None:
            try:
                self._ad.disconnect()
            except Exception:
                pass
            self._ad = None

        self._stop_event.clear()
        self._pause_event.set()
        self._set_status(STATUS_PLOTTING)

        opts = self._snapshot_options()
        self._plot_thread = threading.Thread(
            target=self._plot_svg_worker, args=(svg_path, opts), daemon=True
        )
        self._plot_thread.start()

    def PausePlot(self):
        if self._status == STATUS_PLOTTING:
            self._pause_event.clear()
            self._set_status(STATUS_PAUSED)

    def ResumePlot(self):
        if self._status == STATUS_PAUSED:
            self._pause_event.set()
            self._set_status(STATUS_PLOTTING)

    def StopPlot(self):
        self._stop_event.set()
        self._pause_event.set()
        if self._ad is not None:
            try:
                self._ad.plot_status.stopped = 1
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Speed / options
    # ------------------------------------------------------------------

    def SetSpeed(self, pendown_pct, penup_pct):
        self.ownerComp.par.Speedpendown = int(pendown_pct)
        self.ownerComp.par.Speedpenup = int(penup_pct)
        if self._ad is not None:
            self._ad.options.speed_pendown = int(pendown_pct)
            self._ad.options.speed_penup = int(penup_pct)
            self._ad.options.accel = int(self._par("Accel", 75))
            self._ad.update()

    def SetAccel(self, accel_pct):
        self.ownerComp.par.Accel = int(accel_pct)
        if self._ad is not None:
            self._ad.options.accel = int(accel_pct)
            self._ad.update()

    def SetPenPositions(self, pen_down_pct, pen_up_pct):
        """Update pen-up and pen-down heights on the connected AxiDraw.

        Also writes the values back to the COMP parameters so the UI stays
        in sync."""
        self.ownerComp.par.Penposdown = int(pen_down_pct)
        self.ownerComp.par.Penposup = int(pen_up_pct)
        if self._ad is not None:
            self._ad.options.pen_pos_down = int(pen_down_pct)
            self._ad.options.pen_pos_up = int(pen_up_pct)
            self._ad.update()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _plot_worker(self, polylines, pen):
        try:
            ad = self._ad
            if ad is None:
                return
            for poly in polylines:
                self._pause_event.wait()
                if self._stop_event.is_set() or getattr(ad.plot_status, "stopped", 0):
                    break
                if len(poly) < 2:
                    continue
                ad.draw_path([[float(p[0]), float(p[1])] for p in poly])
                self._points_done += len(poly)
        except Exception as e:
            self._error_msg = str(e)
            debug("AxiDrawExt plot error: " + str(e))
        finally:
            self._plot_thread = None
            self._stop_event.clear()
            self._pause_event.set()
            if self._ad is not None:
                try:
                    self._ad.plot_status.stopped = 0
                    self._apply_pen_options(self._ad, pen)
                    self._ad.penup()
                except Exception:
                    pass
            self._set_status(
                STATUS_CONNECTED if self._ad is not None else STATUS_DISCONNECTED
            )

    def _plot_svg_worker(self, svg_path, opts):
        try:
            ad = axidraw.AxiDraw()
            ad.plot_setup(svg_path)

            ad.options.model = opts["model"]
            ad.options.units = 2
            ad.options.speed_pendown = opts["speed_pendown"]
            ad.options.speed_penup = opts["speed_penup"]
            ad.options.pen_pos_down = opts["pen_pos_down"]
            ad.options.pen_pos_up = opts["pen_pos_up"]
            ad.options.accel = opts["accel"]
            if opts["port"]:
                ad.options.port = opts["port"]

            if self._stop_event.is_set():
                return

            # expose to StopPlot so it can flag plot_status.stopped mid-run
            self._ad = ad
            try:
                ad.plot_status.stopped = 0
            except Exception:
                pass

            ad.plot_run()

        except Exception as e:
            self._error_msg = str(e)
            debug("AxiDrawExt plot error: " + str(e))

        finally:
            self._plot_thread = None
            self._stop_event.clear()
            self._pause_event.set()
            self._ad = None
            self._set_status(STATUS_CONNECTED)
            try:
                ad2 = axidraw.AxiDraw()
                ad2.interactive()
                ad2.options.model = opts["model"]
                if opts["port"]:
                    ad2.options.port = opts["port"]
                if ad2.connect():
                    ad2.penup()
                    ad2.disconnect()
            except Exception:
                pass

    def _apply_pen_options(self, ad, pen):
        """Push pre-snapshotted pen positions onto the AxiDraw options
        object so the next penup/pendown uses them."""
        ad.options.pen_pos_down = pen["pen_pos_down"]
        ad.options.pen_pos_up = pen["pen_pos_up"]

    def _interactive_cmd(self, fn):
        if self._ad is None:
            debug("AxiDrawExt: not connected")
            return
        t = threading.Thread(target=self._run_cmd, args=(fn,), daemon=True)
        t.start()

    def _run_cmd(self, fn):
        try:
            fn(self._ad)
            self._ad.update()
        except Exception as e:
            self._set_error(str(e))

    def _set_status(self, status):
        self._status = status
        self._error_msg = "" if status != STATUS_ERROR else self._error_msg

    def _set_error(self, msg):
        self._error_msg = msg
        self._status = STATUS_ERROR
        debug("AxiDrawExt ERROR: " + msg)

    def _update_status_dat(self):
        try:
            dat = self.ownerComp.op("status")
            if dat:
                dat.clear()
                dat.write("Status:  " + self._status + "\n")
                dat.write("Error:   " + self._error_msg + "\n")
                dat.write("Plotting: " + str(self.IsPlotting) + "\n")
                done = self._points_done
                total = self._points_total
                remaining = max(0, total - done)
                pct = (100.0 * done / total) if total else 0.0
                dat.write(
                    "Progress: {0}/{1} points ({2} remaining, {3:.1f}%)\n".format(
                        done, total, remaining, pct
                    )
                )
        except Exception:
            pass

    def _par(self, name, default):
        try:
            return self.ownerComp.par[name].val
        except Exception:
            return default

    @staticmethod
    def _resample_polyline(poly, min_seg, max_seg):
        """Drop sub-min_seg points (collapse to previous), and subdivide any
        segment longer than max_seg into evenly-spaced points <= max_seg.
        min_seg <= 0 disables the drop; max_seg <= 0 disables subdivision."""
        if len(poly) < 2:
            return poly
        out = [[float(poly[0][0]), float(poly[0][1])]]
        for raw in poly[1:]:
            x, y = float(raw[0]), float(raw[1])
            px, py = out[-1]
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy)
            if min_seg > 0 and d < min_seg:
                continue
            if max_seg > 0 and d > max_seg:
                n = int(math.ceil(d / max_seg))
                for i in range(1, n):
                    t = i / n
                    out.append([px + dx * t, py + dy * t])
            out.append([x, y])
        return out

    def _resample_polylines(self, polylines, min_seg, max_seg):
        if min_seg <= 0 and max_seg <= 0:
            return polylines
        return [self._resample_polyline(p, min_seg, max_seg) for p in polylines]

    def _snapshot_pen(self):
        return {
            "pen_pos_down": int(self._par("Penposdown", 40)),
            "pen_pos_up": int(self._par("Penposup", 60)),
        }

    def _snapshot_options(self):
        return {
            "model": self._model_code(),
            "speed_pendown": int(self._par("Speedpendown", 25)),
            "speed_penup": int(self._par("Speedpenup", 75)),
            "pen_pos_down": int(self._par("Penposdown", 40)),
            "pen_pos_up": int(self._par("Penposup", 60)),
            "accel": int(self._par("Accel", 75)),
            "port": self._par("Port", ""),
        }

    def _snapshot_resample(self):
        return {
            "min_seg": float(self._par("Minsegmm", 0.1)),
            "max_seg": float(self._par("Maxsegmm", 1.5)),
        }

    def _model_code(self):
        """Read the Model parameter ("A1"-"A4") and return the AxiDraw
        API numeric code.  Defaults to A1 (SE/A1) = 5."""
        model_str = self._par("Model", "A1")
        return self._MODEL_MAP.get(model_str, 5)

    def Sync(self):
        """Call this from a Timer CHOP Execute or per-frame Execute DAT on the main thread."""
        self._update_status_dat()

    def _start_tick(self):
        if self._tick_running:
            return
        self._tick_running = True
        self._tick()

    def _tick(self):
        try:
            self._update_status_dat()
        finally:
            run("args[0]._tick()", self, delayFrames=6)
