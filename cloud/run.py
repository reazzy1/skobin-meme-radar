from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

RADAR_ROOT = Path(os.environ.get("RADAR_ROOT", "/opt/radar"))
DATA_DIR = RADAR_ROOT / "data"
DB_PATH = DATA_DIR / "radar.db"
SUBS_PATH = DATA_DIR / "telegram_subscribers.json"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
API = "https://api.telegram.org/bot" + TOKEN if TOKEN else ""
PORT = int(os.environ.get("PORT", "10000"))

DATA_DIR.mkdir(parents=True, exist_ok=True)


def rows(sql, args=()):
    if not DB_PATH.exists():
        return []
    con = sqlite3.connect(str(DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args).fetchall()]
    finally:
        con.close()


def load_subscribers():
    out = set()
    env_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if env_chat:
        out.add(env_chat)
    try:
        out.update(str(x) for x in json.loads(SUBS_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    return out


SUBS = load_subscribers()


def save_subscribers():
    try:
        SUBS_PATH.write_text(json.dumps(sorted(SUBS)), encoding="utf-8")
    except Exception as e:
        print("subscriber save error:", e, flush=True)


def api(method, payload=None, timeout=30):
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    r = requests.post(API + "/" + method, json=payload or {}, timeout=timeout)
    data = r.json()
    if not r.ok or not data.get("ok"):
        raise RuntimeError(data.get("description") or r.text[:300])
    return data.get("result")


def send(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text[:4096],
        "disable_web_page_preview": True,
        "reply_markup": {
            "keyboard": [
                [{"text": "/radar"}, {"text": "/signals"}],
                [{"text": "/status"}, {"text": "/bets"}]
            ],
            "resize_keyboard": True
        }
    }
    try:
        api("sendMessage", payload, 15)
    except Exception as e:
        print("telegram send error:", e, flush=True)


def usd(v):
    try:
        v = float(v or 0)
    except Exception:
        return "$0"
    if abs(v) >= 1000000:
        return "$" + format(v / 1000000, ".2f") + "M"
    if abs(v) >= 1000:
        return "$" + format(v / 1000, ".1f") + "K"
    return "$" + format(v, ".2f")


def status_text():
    rr = rows("SELECT key,value FROM runtime WHERE key IN ('heartbeat','last_cycle_summary')")
    d = {r["key"]: r["value"] for r in rr}
    age = None
    try:
        age = max(0, int(time.time()) - int(d.get("heartbeat")))
    except Exception:
        pass
    try:
        summary = json.loads(d.get("last_cycle_summary") or "{}")
    except Exception:
        summary = {}
    online = age is not None and age < 90
    return (
        "📡 Skobin Meme Radar\n"
        + "Scanner: " + ("online" if online else "offline")
        + ((" · heartbeat " + str(age) + "s") if age is not None else "")
        + "\nDiscovered: " + str(summary.get("discovered", "—"))
        + " · fetched: " + str(summary.get("fetched", "—"))
        + "\nGMGN: " + ("ready" if summary.get("gmgn_ready") else "fallback / not ready")
    )


def radar_text():
    rr = rows(
        """SELECT token,symbol,market_cap,holder_count,holders_per_min,tx_per_min,score,stage
           FROM tokens WHERE last_seen_ts>=?
           ORDER BY score DESC,holders_per_min DESC LIMIT 8""",
        (int(time.time()) - 600,),
    )
    if not rr:
        return "Пока нет свежих кандидатов."
    out = ["🔥 Crowd Launch Radar"]
    for r in rr:
        out.append(
            "\n" + str(r.get("stage") or "DISCOVERED") + " · " + str(r.get("symbol") or "?")
            + " · score " + format(float(r.get("score") or 0), ".0f")
            + "\nMC " + usd(r.get("market_cap"))
            + " · 👥 " + str(int(r.get("holder_count") or 0))
            + " · " + format(float(r.get("holders_per_min") or 0), ".0f") + " H/min"
            + " · " + format(float(r.get("tx_per_min") or 0), ".0f") + " tx/min"
            + "\nhttps://axiom.trade/t/" + str(r.get("token")) + "?chain=sol"
        )
    return "\n".join(out)


def signals_text():
    rr = rows("SELECT message,kind,symbol,token,market_cap,score FROM signals ORDER BY id DESC LIMIT 5")
    if not rr:
        return "Сигналов пока нет."
    out = ["🔔 Последние сигналы"]
    for r in rr:
        msg = (r.get("message") or "").strip()
        if msg:
            out.append("\n" + msg[:700])
        else:
            out.append(
                "\n" + str(r.get("kind")) + " · " + str(r.get("symbol") or "?")
                + " · MC " + usd(r.get("market_cap"))
                + " · score " + format(float(r.get("score") or 0), ".0f")
                + "\nhttps://axiom.trade/t/" + str(r.get("token")) + "?chain=sol"
            )
    return "\n".join(out)


def bets_text():
    rr = rows(
        """SELECT symbol,stake_usd,current_value_usd,pnl_usd,pnl_pct,status
           FROM test_bets ORDER BY id DESC LIMIT 8"""
    )
    if not rr:
        return "🧪 Тест-ставок пока нет."
    out = ["🧪 Последние тест-ставки"]
    for r in rr:
        out.append(
            "\n" + str(r.get("symbol") or "?") + " · " + str(r.get("status"))
            + "\n" + usd(r.get("stake_usd")) + " → " + usd(r.get("current_value_usd"))
            + " · " + format(float(r.get("pnl_pct") or 0), "+.1f") + "%"
            + " (" + format(float(r.get("pnl_usd") or 0), "+.2f") + "$)"
        )
    return "\n".join(out)


def handle(msg):
    chat_id = str((msg.get("chat") or {}).get("id") or "")
    text = (msg.get("text") or "").strip().split("@", 1)[0]
    if not chat_id:
        return
    if text.startswith("/start"):
        SUBS.add(chat_id)
        save_subscribers()
        print("REGISTER_CHAT_ID=" + chat_id, flush=True)
        send(chat_id, "✅ Skobin Meme Radar подключён.\nБуду присылать WATCH / ENTRY / TP / STOP / TRAIL.\nКоманды: /radar /signals /status /bets")
    elif text.startswith("/radar"):
        send(chat_id, radar_text())
    elif text.startswith("/signals"):
        send(chat_id, signals_text())
    elif text.startswith("/status"):
        send(chat_id, status_text())
    elif text.startswith("/bets"):
        send(chat_id, bets_text())
    elif text.startswith("/stop"):
        SUBS.discard(chat_id)
        save_subscribers()
        send(chat_id, "Уведомления отключены. /start — включить снова.")
    elif text.startswith("/help"):
        send(chat_id, "/radar — кандидаты\n/signals — сигналы\n/status — scanner\n/bets — тест-ставки\n/stop — отключить уведомления")


def telegram_loop():
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN is not configured", flush=True)
        while True:
            time.sleep(60)
    offset = 0
    while True:
        try:
            updates = api("getUpdates", {
                "offset": offset,
                "timeout": 20,
                "allowed_updates": ["message"]
            }, 30) or []
            for u in updates:
                offset = max(offset, int(u.get("update_id", 0)) + 1)
                if u.get("message"):
                    handle(u["message"])
        except Exception as e:
            print("telegram polling error:", e, flush=True)
            time.sleep(3)


def relay_loop():
    rr = rows("SELECT COALESCE(MAX(id),0) n FROM signals")
    last_id = int(rr[0]["n"] if rr else 0)
    while True:
        try:
            fresh = rows("SELECT id,message FROM signals WHERE id>? ORDER BY id ASC", (last_id,))
            for r in fresh:
                last_id = max(last_id, int(r["id"]))
                msg = (r.get("message") or "").strip()
                if not msg:
                    continue
                for chat_id in list(SUBS):
                    send(chat_id, msg)
        except Exception as e:
            print("relay error:", e, flush=True)
        time.sleep(3)


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok":true,"service":"skobin-meme-radar-bot"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def health_loop():
    ThreadingHTTPServer(("0.0.0.0", PORT), Health).serve_forever()


def configure_gmgn():
    key = os.environ.get("GMGN_API_KEY", "").strip()
    if not key:
        print("GMGN_API_KEY not set; fallback discovery may be used", flush=True)
        return
    try:
        p = subprocess.run(
            ["gmgn-cli", "config", "--apply", key],
            cwd=str(RADAR_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        print("GMGN config:", "ready" if p.returncode == 0 else "failed", flush=True)
    except Exception as e:
        print("GMGN config error:", e, flush=True)


def main():
    configure_gmgn()
    engine = subprocess.Popen([sys.executable, str(RADAR_ROOT / "engine.py")], cwd=str(RADAR_ROOT))

    def stop(*_):
        try:
            engine.terminate()
        except Exception:
            pass
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    threading.Thread(target=health_loop, daemon=True).start()
    threading.Thread(target=relay_loop, daemon=True).start()
    print("Telegram bot service started", flush=True)
    telegram_loop()


if __name__ == "__main__":
    main()
