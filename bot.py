import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot
import logging
import os

BOT_TOKEN = os.environ.get('8274488764:AAHfo87eHioo2Iz_Ii2kyVIPHDcIuc6hnRo')
GROUP_ID = int(os.environ.get('-1005019746478'))

SONY = "https://raw.githubusercontent.com/drmlive/sliv-live-events/main/sonyliv.json"
FANCODE = "https://raw.githubusercontent.com/drmlive/fancode-live-events/main/fancode.json"

logging.basicConfig(level=logging.INFO)
bot = None
posted = {}

async def fetch(url):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(30)) as r:
                return await r.json() if r.status == 200 else None
    except: return None

def parse_time(t):
    try:
        if ' ' in str(t) and '-' in str(t):
            p = t.split(' ')
            d = p[2].split('-')
            return datetime.strptime(f"{d[2]}-{d[1]}-{d[0]} {p[0]} {p[1]}", "%Y-%m-%d %I:%M:%S %p")
        return datetime.fromisoformat(str(t).replace('Z', ''))
    except: return None

def status(e, src):
    now = datetime.now()
    if src == "sony" and e.get("isLive"): return "LIVE", None
    
    st = parse_time(e.get("start_time") or e.get("startTime"))
    if not st: return "UNKNOWN", None
    
    st = st.replace(tzinfo=None) if st.tzinfo else st
    diff = (st - now).total_seconds()
    
    if -900 <= diff <= 10800: return "LIVE", st
    if diff > 900: return "UPCOMING", st
    return "FINISHED", st

def time_left(st):
    if not st: return None
    diff = (st - datetime.now()).total_seconds()
    if diff < 0: return None
    h, m = int(diff//3600), int((diff%3600)//60)
    return f"{h}h {m}m" if h else f"{m}m"

def msg(e, src, stat, st):
    title = e.get("match_name") or e.get("title") or "Sports"
    if e.get("team_1") and e.get("team_2"):
        title = f"{e['team_1']} vs {e['team_2']}"
    
    cat = e.get("event_category") or e.get("sport") or "Sports"
    ch = "Sony LIV" if src == "sony" else "FanCode"
    
    url = (e.get("dai_url") or e.get("pub_url") or e.get("video_url")) if src == "sony" else (e.get("adfree_url") or e.get("dai_url"))
    if not url: url = f"https://www.fancode.com/match/{e.get('match_id','')}"
    
    m = f"🏆 *{title}*\n\n🏅 {cat}\n📺 {ch}\n"
    
    if stat == "LIVE":
        m += f"🔴 *LIVE NOW*\n\n🔗 `{url}`\n"
    else:
        tl = time_left(st)
        m += f"⏰ *Starts in: {tl}*\n\n🔗 URL Active in: *{tl}*\n" if tl else "📅 Starting Soon\n\n"
    
    m += "\n━━━━━━━━━━━━━\n🤖 StreamFlex\n👤 Shubham Bhandari\n⚡@StreamFlex19"
    return m

async def post(e, src, stat, st, eid):
    global posted
    try:
        txt = msg(e, src, stat, st)
        thumb = e.get("image") or e.get("poster") or e.get("thumbnail")
        
        if stat == "LIVE":
            if eid in posted:
                try:
                    await bot.delete_message(GROUP_ID, posted[eid])
                    del posted[eid]
                except: pass
            
            if thumb:
                await bot.send_photo(GROUP_ID, thumb, caption=txt, parse_mode='Markdown')
            else:
                await bot.send_message(GROUP_ID, txt, parse_mode='Markdown')
            logging.info(f"✅ LIVE: {e.get('title')}")
        
        else:
            tl = time_left(st)
            if tl:
                mins = int(tl.replace('h',' ').replace('m','').split()[-1])
                if mins <= 15 or eid in posted:
                    if eid in posted:
                        try:
                            if thumb:
                                await bot.edit_message_caption(GROUP_ID, posted[eid], caption=txt, parse_mode='Markdown')
                            else:
                                await bot.edit_message_text(GROUP_ID, posted[eid], text=txt, parse_mode='Markdown')
                        except: pass
                    else:
                        if thumb:
                            m = await bot.send_photo(GROUP_ID, thumb, caption=txt, parse_mode='Markdown')
                        else:
                            m = await bot.send_message(GROUP_ID, txt, parse_mode='Markdown')
                        posted[eid] = m.message_id
    except Exception as e:
        logging.error(f"Error: {e}")

async def process():
    logging.info("🔍 Checking...")
    
    data = await fetch(SONY)
    if data:
        events = data if isinstance(data, list) else data.get("events", [])
        for e in events:
            try:
                eid = f"s{e.get('id')}"
                s, st = status(e, "sony")
                if s in ["LIVE", "UPCOMING"]:
                    await post(e, "sony", s, st, eid)
                    await asyncio.sleep(1)
            except: pass
    
    data = await fetch(FANCODE)
    if data:
        events = data if isinstance(data, list) else data.get("events", [])
        for e in events:
            try:
                eid = f"f{e.get('match_id')}"
                s, st = status(e, "fancode")
                if s in ["LIVE", "UPCOMING"]:
                    await post(e, "fancode", s, st, eid)
                    await asyncio.sleep(1)
            except: pass

async def main():
    global bot
    bot = Bot(BOT_TOKEN)
    logging.info("🤖 Bot Started!")
    await process()

if __name__ == "__main__":
    asyncio.run(main())
