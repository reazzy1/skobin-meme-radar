from pathlib import Path

root = Path("/tmp/meme-radar-app")
p = root / "desktop_app.py"
text = p.read_text(encoding="utf-8", errors="replace")

# v2.9 is a thin UI wrapper over desktop_app_v28.py, so fix scanner recovery
# in the wrapper by overriding the two affected methods.
if "import subprocess" not in text:
    text = text.replace(
        "import base64\nimport tkinter as tk\n",
        "import base64\nimport os\nimport subprocess\nimport sys\nfrom pathlib import Path\nimport tkinter as tk\nfrom tkinter import messagebox\n",
        1,
    )

methods = '''    def ensure_engine(self):
        hb=get_runtime("heartbeat")
        alive=False
        if hb:
            try:
                alive=now_ts()-int(hb["value"])<90
            except Exception:
                pass

        # The updater removes engine.pid when it stops the scanner. Do not trust
        # a stale heartbeat if the process marker is already gone.
        if alive and PID_FILE.exists():
            return

        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass

        cmd=[str(Path(sys.executable)),str(ROOT/"engine.py")]
        kw={"cwd":str(ROOT)}
        if os.name=="nt":
            kw["creationflags"]=0x08000000
        try:
            subprocess.Popen(cmd,**kw)
            if hasattr(self,"engine_status"):
                self.engine_status.config(text="● Scanner запускается…",fg=YELLOW)
        except Exception as e:
            if hasattr(self,"engine_status"):
                self.engine_status.config(text="● Scanner ошибка запуска",fg=RED)
            messagebox.showerror("Scanner",str(e))

    def tick(self):
        try:
            self.ensure_engine()
            self.update_status()
            self.refresh_current()
            while True:
                try:
                    fn,args=self.jobq.get_nowait()
                    fn(*args)
                except queue.Empty:
                    break
        finally:
            self.after(7000,self.tick)

'''

if "    def ensure_engine(self):" not in text:
    marker = "    def _build(self):\n"
    if marker not in text:
        raise SystemExit("_build marker not found")
    text = text.replace(marker, methods + marker, 1)

text = text.replace('self.title(f"Skobin Meme Radar 2.9.0")','self.title(f"Skobin Meme Radar 2.9.1")',1)
p.write_text(text, encoding="utf-8")
(root / "VERSION").write_text("2.9.1\n", encoding="utf-8")
