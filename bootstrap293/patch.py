from pathlib import Path

root = Path("/tmp/meme-radar-app")

# Telegram helper: local token + auto-detect Chat ID after user sends /start.
tg = root / "core" / "telegram.py"
t = tg.read_text(encoding="utf-8")
if "def detect_chat_id(" not in t:
    t += r'''

def detect_chat_id():
    """Find the most recent chat that messaged the bot."""
    token = env_value("TELEGRAM_BOT_TOKEN")
    if not token:
        return False, "Сначала вставь Bot token и нажми «Сохранить»."
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"limit": 100, "timeout": 0, "allowed_updates": '["message"]'},
            timeout=15,
        )
        data = r.json()
        if not r.ok or not data.get("ok"):
            return False, data.get("description", r.text[:300])
        updates = data.get("result") or []
        for upd in reversed(updates):
            msg = upd.get("message") or {}
            chat = msg.get("chat") or {}
            cid = chat.get("id")
            if cid is not None:
                who = chat.get("username") or chat.get("first_name") or str(cid)
                return True, {"chat_id": str(cid), "name": who}
        return False, "Сообщений от тебя ещё нет. Открой своего бота в Telegram, нажми Start или отправь /start, затем нажми «Найти Chat ID» ещё раз."
    except Exception as e:
        return False, str(e)
'''
tg.write_text(t, encoding="utf-8")

app = root / "desktop_app.py"
a = app.read_text(encoding="utf-8")
a = a.replace(
    "from core.telegram import send as tg_send",
    "from core.telegram import send as tg_send, get_me as tg_get_me, detect_chat_id as tg_detect_chat_id"
)

old_ui = """        tg=tk.LabelFrame(inner,text=' Telegram ',bg=PANEL,fg=TEXT,padx=12,pady=12); tg.pack(fill='x',pady=(0,12))
        self.tg_token=tk.StringVar(value=env_value('TELEGRAM_BOT_TOKEN')); self.tg_chat=tk.StringVar(value=env_value('TELEGRAM_CHAT_ID'))
        tk.Label(tg,text='Bot token',bg=PANEL,fg=MUTED).grid(row=0,column=0,sticky='w'); ttk.Entry(tg,textvariable=self.tg_token,width=48,show='•').grid(row=0,column=1,sticky='ew',padx=8)
        tk.Label(tg,text='Chat ID',bg=PANEL,fg=MUTED).grid(row=1,column=0,sticky='w',pady=8); ttk.Entry(tg,textvariable=self.tg_chat,width=48).grid(row=1,column=1,sticky='ew',padx=8,pady=8)
        ttk.Button(tg,text='Сохранить',command=self.save_telegram).grid(row=2,column=0,sticky='w'); ttk.Button(tg,text='Тест',command=self.test_telegram).grid(row=2,column=1,sticky='w',padx=8)
"""
new_ui = """        tg=tk.LabelFrame(inner,text=' Telegram ',bg=PANEL,fg=TEXT,padx=12,pady=12); tg.pack(fill='x',pady=(0,12))
        self.tg_token=tk.StringVar(value=env_value('TELEGRAM_BOT_TOKEN')); self.tg_chat=tk.StringVar(value=env_value('TELEGRAM_CHAT_ID'))
        tk.Label(tg,text='Bot token',bg=PANEL,fg=MUTED).grid(row=0,column=0,sticky='w')
        ttk.Entry(tg,textvariable=self.tg_token,width=48,show='•').grid(row=0,column=1,columnspan=3,sticky='ew',padx=8)
        tk.Label(tg,text='Chat ID',bg=PANEL,fg=MUTED).grid(row=1,column=0,sticky='w',pady=8)
        ttk.Entry(tg,textvariable=self.tg_chat,width=32).grid(row=1,column=1,sticky='ew',padx=8,pady=8)
        ttk.Button(tg,text='Найти Chat ID',command=self.detect_telegram_chat).grid(row=1,column=2,sticky='w',padx=(0,8))
        ttk.Button(tg,text='Сохранить',command=self.save_telegram).grid(row=2,column=0,sticky='w')
        ttk.Button(tg,text='Тест',command=self.test_telegram).grid(row=2,column=1,sticky='w',padx=8)
        self.tg_watch=tk.BooleanVar(value=bool(self.cfg.get('telegram',{}).get('notify_watch',True)))
        self.tg_entry=tk.BooleanVar(value=bool(self.cfg.get('telegram',{}).get('notify_entry',True)))
        self.tg_exits=tk.BooleanVar(value=bool(self.cfg.get('telegram',{}).get('notify_exits',True)))
        ttk.Checkbutton(tg,text='WATCH',variable=self.tg_watch).grid(row=3,column=0,sticky='w',pady=(10,0))
        ttk.Checkbutton(tg,text='ENTRY',variable=self.tg_entry).grid(row=3,column=1,sticky='w',pady=(10,0))
        ttk.Checkbutton(tg,text='TP / STOP / TRAIL',variable=self.tg_exits).grid(row=3,column=2,columnspan=2,sticky='w',pady=(10,0))
        tk.Label(tg,text='Токен хранится только локально в .env. Чтобы найти Chat ID: сначала напиши своему боту /start.',bg=PANEL,fg=MUTED,wraplength=780,justify='left').grid(row=4,column=0,columnspan=4,sticky='w',pady=(8,0))
        tg.grid_columnconfigure(1,weight=1)
"""
if old_ui not in a:
    raise SystemExit("telegram UI block not found")
a = a.replace(old_ui, new_ui)

old_methods = """    def save_telegram(self): write_env_values({'TELEGRAM_BOT_TOKEN':self.tg_token.get().strip(),'TELEGRAM_CHAT_ID':self.tg_chat.get().strip()}); messagebox.showinfo('Telegram','Сохранено')
    def test_telegram(self): self.save_telegram(); ok,msg=tg_send('✅ Skobin Meme Radar: Telegram настроен.'); messagebox.showinfo('Telegram','Сообщение отправлено' if ok else str(msg))
"""
new_methods = """    def save_telegram(self, show_message=True):
        write_env_values({
            'TELEGRAM_BOT_TOKEN':self.tg_token.get().strip(),
            'TELEGRAM_CHAT_ID':self.tg_chat.get().strip()
        })
        self.cfg.setdefault('telegram',{})['notify_watch']=bool(self.tg_watch.get())
        self.cfg['telegram']['notify_entry']=bool(self.tg_entry.get())
        self.cfg['telegram']['notify_exits']=bool(self.tg_exits.get())
        save_config(self.cfg)
        if show_message:
            messagebox.showinfo('Telegram','Сохранено. Уведомления начнут работать со следующего цикла scanner.')

    def detect_telegram_chat(self):
        token=self.tg_token.get().strip()
        if not token:
            messagebox.showwarning('Telegram','Сначала вставь новый Bot token.')
            return
        write_env_values({'TELEGRAM_BOT_TOKEN':token})
        ok,res=tg_detect_chat_id()
        if not ok:
            messagebox.showwarning('Telegram',str(res))
            return
        self.tg_chat.set(str(res.get('chat_id')))
        self.save_telegram(show_message=False)
        messagebox.showinfo('Telegram',f"Chat ID найден: {res.get('name')}\\nТеперь нажми «Тест».")

    def test_telegram(self):
        self.save_telegram(show_message=False)
        ok,me=tg_get_me()
        if not ok:
            messagebox.showerror('Telegram',f'Bot token не работает: {me}')
            return
        ok,msg=tg_send('✅ Skobin Meme Radar подключён. WATCH / ENTRY / TP / STOP будут приходить сюда.')
        messagebox.showinfo('Telegram','Тестовое сообщение отправлено.' if ok else str(msg))
"""
if old_methods not in a:
    raise SystemExit("telegram methods block not found")
a = a.replace(old_methods, new_methods)
app.write_text(a, encoding="utf-8")

# Add direct Axiom links to WATCH / ENTRY messages.
engine = root / "engine.py"
e = engine.read_text(encoding="utf-8")
watch_old = '        f"{p.url}"\n    )\n    add_signal(p.token,p.symbol,"WATCH"'
watch_new = '        f"Axiom: https://axiom.trade/t/{p.token}?chain=sol\\\\n"\n        f"{p.url}"\n    )\n    add_signal(p.token,p.symbol,"WATCH"'
if watch_old in e:
    e = e.replace(watch_old, watch_new, 1)

entry_old = '        f"{p.url}"\n    )\n    add_signal(p.token,p.symbol,"ENTRY"'
entry_new = '        f"Axiom: https://axiom.trade/t/{p.token}?chain=sol\\\\n"\n        f"{p.url}"\n    )\n    add_signal(p.token,p.symbol,"ENTRY"'
if entry_old in e:
    e = e.replace(entry_old, entry_new, 1)
engine.write_text(e, encoding="utf-8")

(root / "VERSION").write_text("2.9.3\\n", encoding="utf-8")
