from pathlib import Path
root = Path("/tmp/meme-radar-app")
p = root / "desktop_app.py"
text = p.read_text(encoding="utf-8", errors="replace")
print("LEN", len(text))
print(text[:12000])
raise SystemExit("diagnostic stop")
