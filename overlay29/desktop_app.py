from __future__ import annotations

import base64
import tkinter as tk

from desktop_app_v28 import *
from desktop_app_v28 import MemeRadarApp as BaseMemeRadarApp
from core import gmgn
from core.db import get_runtime
from core.utils import now_ts

ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAACkUlEQVR42u1bsU7DMBBtrGwwwELXdMnerTsDfwArG8oXdGNFER8QsXWFP2CoWJnIngG6dmJhh8mViRz7bN/ZceOTkCrh2n7P753PbpKdnF38ziYcbDbxSAQkAhIBiYBEwJQj9zFI2dbgtt1y7ZWAjKoQMgEdkgxUAjBA+yYDhQAIcAgA135+ru8On09fnvwQMDRpjBWD9i0C74eOCIY9wW65RpPrUF+YVrNSwBDwELvJx8On9nsqFbBYwFONk7uAN5kQVqLkbbBsALaADXiXSZr0r7IBSRLUTa5sa+cVgvSBYQmQAsSJQMDbTNj2e1WzP3x+fLvHrwNMpI+VICH9iMDF2K42RmMqCXABT1EI8T5V4E3HZxi+pwAv66dsayn4pprPmmqOuw1Ck5hJfnAhYWjVh4CXbQ2aT059eMFOdCrw3XJtPKcc25+2RPE2kGQnet01GIVXMVRSNXsr8OJcIGMzCtCQ06L4Zyt5jHI497XyqrZifX/5fqsEbuNzcgtgbItVs9eCp7itIr8Wh4LXFTZU1WceCjQ0y8v2c0wbePldQLZqMrmLkqe8YfZqARvwPiOIArarzT8SQgAPpoC+zzGruigIEBOa6dn9aCzgcqt0NBZwIcuGoK/dLg4CTMFBCOLgZSSwMYPHyA+v5zdKJbDYwLvmh0VRjD8HQFde166/+n3woyKAg4EcsTkwmaf7bXSRxfKssAqYuLJlW2vbBK8DsBJaP7FdfT+DfB+VAkwlbQJ+9IWQTvY6cFFXglDPL4rCSvpRKMAkmXES+P+h6hhtDpBtcTJQrj/NjVYBfbA68Ed5GlTJGevckMX20hT2U2psyuCjqgSpHsKI8oUJzHvELL04OfFIBCQCEgGJgEnHH/8YcrzWmBZdAAAAAElFTkSuQmCC"

class MemeRadarApp(BaseMemeRadarApp):
    def __init__(self):
        super().__init__()
        self.title(f"Skobin Meme Radar 2.9.0")
        try:
            self._new_icon = tk.PhotoImage(data=ICON_B64)
            self.iconphoto(True, self._new_icon)
        except Exception:
            pass
        self.update_status()

    def _build(self):
        super()._build()
        self.feed_detail = tk.Label(
            self.status_box,
            text="",
            bg="#0d131a",
            fg=MUTED,
            font=("Segoe UI", 8),
            justify="left",
            wraplength=185,
        )
        self.feed_detail.pack(anchor="w", pady=(3, 0))

    def update_status(self):
        super().update_status()
        if not gmgn.installed():
            ok = False
            msg = "gmgn-cli не установлен"
        else:
            ok, raw = gmgn.check_config()
            msg = "New Creation feed активен" if ok else (raw or "API key / config не готов")
        self.gmgn_status.config(
            text="● GMGN " + ("New Creation" if ok else "НЕ ГОТОВ"),
            fg=GREEN if ok else RED,
        )
        if hasattr(self, "feed_detail"):
            self.feed_detail.config(
                text=("Ищем новые токены + holders" if ok else "DEX fallback неполный: Crowd WATCH/ENTRY почти не будет. Настройки → GMGN."),
                fg=GREEN if ok else YELLOW,
            )
        if hasattr(self, "gmgn_info"):
            self.gmgn_info.config(
                text=("🟢 " + msg if ok else "🔴 " + str(msg)[:180]),
                fg=GREEN if ok else RED,
            )

if __name__ == "__main__":
    MemeRadarApp().mainloop()
