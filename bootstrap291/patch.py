from pathlib import Path
root = Path("/tmp/meme-radar-app")
p = root / "desktop_app.py"
text = p.read_text(encoding="utf-8")
for needle in ("def ensure_engine", "def tick"):
    i=text.find(needle)
    print("=== ", needle, " @ ", i, " ===")
    print(text[max(0,i-200):i+1800] if i >= 0 else "NOT FOUND")
raise SystemExit("diagnostic stop")
