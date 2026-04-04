"""
Lightweight HTTP API server for printing status + LED control.

Endpoints:
  GET /printingstatus  → JSON printer state
  GET /ledstatus       → JSON LED state (for ESP8266 polling)
Port: 7177
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

logger = logging.getLogger(__name__)

API_PORT = 7177


def _safe_round(value, digits: int = 2):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


class _StatusHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler — serves /printingstatus and /ledstatus."""

    # Shared references, set before server starts.
    klippy = None
    led_controller = None

    # ------------------------------------------------------------------ #
    #  HTTP routing                                                        #
    # ------------------------------------------------------------------ #

    def do_GET(self):
        path = self.path.rstrip("/")
        if path == "/printingstatus":
            body = json.dumps(self._build_print_payload(), ensure_ascii=False, indent=2).encode("utf-8")
            self._respond(200, "application/json", body)
        elif path == "/ledstatus":
            body = json.dumps(self._build_led_payload(), ensure_ascii=False, indent=2).encode("utf-8")
            self._respond(200, "application/json", body)
        else:
            self._respond(404, "application/json", b'{"error":"not found"}')

    def do_OPTIONS(self):
        """Support simple CORS pre-flight."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------ #
    #  Payload builders                                                    #
    # ------------------------------------------------------------------ #

    def _build_led_payload(self) -> dict:
        lc = self.led_controller
        if lc is None:
            return {"error": "led_controller not ready"}
        return lc.to_dict()

    def _build_print_payload(self) -> dict:
        kl = self.klippy
        if kl is None:
            return {"error": "klippy not ready"}

        # --- ETA / finish time ---------------------------------------- #
        try:
            eta_td: timedelta = kl._get_eta()  # pylint: disable=protected-access
            eta_seconds = int(eta_td.total_seconds())
            eta_formatted = str(eta_td)
            finish_time = (datetime.now() + eta_td).strftime("%Y-%m-%d %H:%M")
        except Exception:
            eta_seconds = 0
            eta_formatted = ""
            finish_time = ""

        # --- Filament weight used ------------------------------------- #
        try:
            filament_weight_used = _safe_round(kl._filament_weight_used())  # pylint: disable=protected-access
        except Exception:
            filament_weight_used = 0.0

        # --- Sensors (temperatures, fans, heaters) -------------------- #
        sensors: dict = {}
        for name, vals in (kl._sensors_dict or {}).items():  # pylint: disable=protected-access
            sensors[name] = {k: _safe_round(v) if isinstance(v, float) else v for k, v in vals.items()}

        # --- Power / moonraker devices -------------------------------- #
        power_devices: dict = {}
        for name, vals in (kl._power_devices or {}).items():  # pylint: disable=protected-access
            power_devices[name] = dict(vals)

        # --- Heating detection --------------------------------------- #
        heating = False
        if not kl.printing:
            for vals in sensors.values():
                if vals.get("target", 0) > 0:
                    heating = True
                    break

        return {
            # ---- Connection / state ---------------------------------- #
            "connected":    kl.connected,
            "state":        kl.state,
            "state_message": kl.state_message or "",

            # ---- Print flags ---------------------------------------- #
            "printing": kl.printing,
            "paused":   kl.paused,
            "heating":  heating,

            # ---- File ------------------------------------------------ #
            "filename":           kl.printing_filename or "",
            "filename_with_time": kl.printing_filename_with_time if kl.printing_filename else "",

            # ---- Progress ------------------------------------------- #
            "progress_percent":     _safe_round(kl.printing_progress * 100),
            "vsd_progress_percent": _safe_round(kl.vsd_progress * 100),
            "height_mm":            _safe_round(kl.printing_height),

            # ---- Time ----------------------------------------------- #
            "print_duration_seconds":       int(kl.printing_duration),
            "print_duration_formatted":     str(timedelta(seconds=int(kl.printing_duration))),
            "file_estimated_time_seconds":  int(kl.file_estimated_time),
            "file_estimated_time_formatted": str(timedelta(seconds=int(kl.file_estimated_time))),
            "eta_seconds":   eta_seconds,
            "eta_formatted": eta_formatted,
            "finish_time":   finish_time,

            # ---- Filament ------------------------------------------- #
            "filament_used_mm":      _safe_round(kl.filament_used),
            "filament_used_m":       _safe_round(kl.filament_used / 1000, 3),
            "filament_total_mm":     _safe_round(kl.filament_total),
            "filament_total_m":      _safe_round(kl.filament_total / 1000, 3),
            "filament_weight_total_g": _safe_round(kl.filament_weight),
            "filament_weight_used_g":  filament_weight_used,

            # ---- Temperatures / sensors ----------------------------- #
            "sensors": sensors,

            # ---- Power devices -------------------------------------- #
            "power_devices": power_devices,
        }

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _respond(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):  # suppress default stderr logging
        logger.debug("API %s", fmt % args)


# --------------------------------------------------------------------------- #
#  Public interface                                                             #
# --------------------------------------------------------------------------- #

def start_api_server(klippy, led_controller=None, logging_handler: Optional[logging.Handler] = None) -> HTTPServer:
    """
    Start the status API on port 7177 in a daemon thread.
    Returns the HTTPServer instance (can be used to .shutdown() later).
    """
    if logging_handler:
        logger.addHandler(logging_handler)

    _StatusHandler.klippy = klippy
    _StatusHandler.led_controller = led_controller

    server = HTTPServer(("0.0.0.0", API_PORT), _StatusHandler)
    thread = threading.Thread(target=server.serve_forever, name="api_server", daemon=True)
    thread.start()

    logger.info(
        "API started → http://0.0.0.0:%d/printingstatus  |  http://0.0.0.0:%d/ledstatus",
        API_PORT, API_PORT,
    )
    return server
