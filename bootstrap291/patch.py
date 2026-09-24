from pathlib import Path
import re

root = Path("/tmp/meme-radar-app")
p = root / "desktop_app.py"
text = p.read_text(encoding="utf-8")

new_ensure = '''    def ensure_engine(self):
        # A recent heartbeat alone is not enough: updater can stop engine.py
        # while its last heartbeat remains fresh.
        hb=get_runtime('heartbeat')
        heartbeat_alive=False
        if hb:
            try: heartbeat_alive=now_ts()-int(hb['value'])<90
            except: pass

        pid_present = PID_FILE.exists()
        if heartbeat_alive and pid_present:
            return

        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass

        pyw=Path(sys.executable)
        cmd=[str(pyw),str(ROOT/'engine.py')]
        kw={'cwd':str(ROOT)}
        if os.name=='nt':
            kw['creationflags']=0x08000000
        try:
            subprocess.Popen(cmd,**kw)
            if hasattr(self,'engine_status'):
                self.engine_status.config(text='● Scanner запускается…',fg=YELLOW)
        except Exception as e:
            if hasattr(self,'engine_status'):
                self.engine_status.config(text='● Scanner ошибка запуска',fg=RED)
            messagebox.showerror('Scanner',str(e))

'''

text, n = re.subn(
    r"    def ensure_engine\(self\):.*?(?=    def stop_engine\(self\):)",
    new_ensure,
    text,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("ensure_engine patch target not found")

old_tick = """    def tick(self):
        try:
            self.update_status(); self.refresh_current()
"""
new_tick = """    def tick(self):
        try:
            self.ensure_engine()
            self.update_status(); self.refresh_current()
"""
if old_tick in text:
    text = text.replace(old_tick, new_tick, 1)
elif "            self.ensure_engine()\n            self.update_status(); self.refresh_current()" not in text:
    raise SystemExit("tick patch target not found")

p.write_text(text, encoding="utf-8")
(root / "VERSION").write_text("2.9.1\n", encoding="utf-8")
