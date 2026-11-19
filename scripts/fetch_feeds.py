import json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
FEEDS = [
("The Daily Star","Bangladesh","https://www.thedailystar.net/frontpage/rss.xml"),
("bdnews24.com","Bangladesh","https://bdnews24.com/?widgetName=rssfeed&widgetId=1150&getXmlFeed=true"),
("Prothom Alo","Bangladesh","https://www.prothomalo.com/feed/"),
("Dhaka Tribune","Bangladesh","https://www.dhakatribune.com/feed"),
("The Business Standard","Economy & Banking","https://www.tbsnews.net/rss.xml"),
("The Financial Express","Economy & Banking","https://thefinancialexpress.com.bd/rss"),
("BBC World","International","https://feeds.bbci.co.uk/news/world/rss.xml"),
("BBC Business","Economy & Banking","https://feeds.bbci.co.uk/news/business/rss.xml"),
("The Guardian Opinion","English Editorials","https://www.theguardian.com/commentisfree/rss"),
("Project Syndicate","English Editorials","https://www.project-syndicate.org/rss")]
def clean(s):
 return re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()
def val(root,name):
 for e in root.iter():
  if e.tag.split("}")[-1].lower()==name.lower(): return e.text or ""
 return ""
articles=[]
for source,category,url in FEEDS:
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"EditorialHub/1.0"})
  root=ET.fromstring(urllib.request.urlopen(req,timeout=18).read())
  entries=[e for e in root.iter() if e.tag.split("}")[-1].lower() in ("item","entry")]
  for e in entries[:30]:
   title=clean(val(e,"title")); link=val(e,"link").strip()
   if not link:
    for c in e:
     if c.tag.split("}")[-1].lower()=="link": link=c.attrib.get("href",""); break
   summary=clean(val(e,"description") or val(e,"summary") or val(e,"content"))
   date=val(e,"pubDate") or val(e,"published") or val(e,"updated")
   if title and link.startswith("http"):
    articles.append({"title":title,"link":link,"summary":summary[:360],"date":date,"source":source,"category":category})
 except Exception as ex: print("Feed failed:",source,str(ex))
seen=set(); unique=[]
for a in articles:
 if a["link"] not in seen: seen.add(a["link"]); unique.append(a)
unique.sort(key=lambda a:a.get("date",""),reverse=True)
with open("feed.json","w",encoding="utf-8") as f:
 json.dump({"updated":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),"articles":unique[:180]},f,ensure_ascii=False,indent=2)
print("Wrote",min(len(unique),180),"articles")
