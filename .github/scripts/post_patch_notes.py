"""Posts one version's patch notes from index.html to a Discord channel (webhook in the DISCORD_WEBHOOK secret).
Usage: python post_patch_notes.py [versions]   e.g. v1.0.10, or several: v1.0.7,v1.0.8 · none = the newest notes on the page
Every post ends with a "How to update" section.
DRY_RUN=1 prints the message instead of sending it."""
import html, json, os, re, sys, time, urllib.request

page = open("index.html", encoding="utf-8").read()
notes = []
for art in re.findall(r'<article class="rel">(.*?)</article>', page, re.S):
    v = re.search(r'<div class="v">(.*?)</div>', art); d = re.search(r'<div class="d">(.*?)</div>', art)
    if not v or v.group(1).strip() in ("", "Next"): continue
    items = re.findall(r"<li>(.*?)</li>", art, re.S)
    notes.append((v.group(1).strip(), html.unescape(d.group(1).strip()) if d else "", items))
if not notes: sys.exit("no patch notes found in index.html")

UPDATE = ("Open Ashen Depths and click **Update** on the title screen. "
          "The game downloads the new version, installs it and restarts by itself. Your heroes are kept.")
def md(s):
    s = re.sub(r"</?b>", "**", s); s = re.sub(r"</?i>", "*", s); s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

def message(ver, sub, items):
    body = "\n".join("• " + md(i) for i in items)
    if len(body) > 3800: body = body[:3790].rsplit("\n", 1)[0] + "\n…"
    return {
        "username": "Ashen Depths",
        "embeds": [{
            "title": f"Ashen Depths {ver} is out",
            "url": "https://github.com/wadski/ashen_depths/releases",
            "description": (f"*{sub}*\n\n" if sub else "") + body,
            "color": 0xD6B066,
            "fields": [{"name": "How to update", "value": UPDATE}],
            "footer": {"text": "Made by wadski"},
        }],
    }

wanted = [w.strip() for w in (sys.argv[1] if len(sys.argv) > 1 else "").split(",") if w.strip()]
wanted = [w if w.startswith("v") else "v" + w for w in wanted]
picks = [next((n for n in notes if n[0] == w), None) for w in wanted] if wanted else [notes[0]]
missing = [w for w, p in zip(wanted, picks) if p is None]
if missing: sys.exit("no patch notes for " + ", ".join(missing) + " in index.html")

hook = os.environ.get("DISCORD_WEBHOOK")
for ver, sub, items in picks:
    msg = message(ver, sub, items)
    if os.environ.get("DRY_RUN") == "1": print(json.dumps(msg, indent=1, ensure_ascii=False)); continue
    if not hook: sys.exit("DISCORD_WEBHOOK is not set")
    req = urllib.request.Request(hook, data=json.dumps(msg).encode(), headers={"Content-Type": "application/json", "User-Agent": "ashen-depths-notes"})
    urllib.request.urlopen(req).read(); print(f"posted {ver}"); time.sleep(2)
