from pathlib import Path

root = Path("/tmp/meme-radar-app")
p = root / "desktop_app.py"
text = p.read_text(encoding="utf-8")

# Fix the post-update scanner deadlock:
# old heartbeat can still look fresh although updater already killed engine.py.
if "        if alive: return" in text:
    text = text.replace(
        "        if alive: return",
        "        if alive and PID_FILE.exists(): return",
        1,
    )
elif "        if heartbeat_alive and pid_present:" not in text:
    raise SystemExit("ensure_engine patch target not found")

# Also self-heal on every UI tick if the background scanner dies later.
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
