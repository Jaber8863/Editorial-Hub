import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Ten major Bangla newspapers. Some publishers expose a general RSS feed rather
# than a separate editorial-only feed; items are therefore not falsely labelled
# as editorials unless the publisher provides a dedicated opinion feed.
BANGLA_FEEDS = [
    ("প্রথম আলো", "বাংলা সংবাদপত্র", "https://www.prothomalo.com/feed/"),
    ("যুগান্তর", "বাংলা সংবাদপত্র", "https://www.jugantor.com/rss.xml"),
    ("কালের কণ্ঠ", "বাংলা সংবাদপত্র", "https://www.kalerkantho.com/rss.xml"),
    ("সমকাল", "বাংলা সংবাদপত্র", "https://samakal.com/rss.xml"),
    ("দৈনিক ইত্তেফাক", "বাংলা সংবাদপত্র", "https://www.ittefaq.com.bd/rss"),
    ("বাংলাদেশ প্রতিদিন", "বাংলা সংবাদপত্র", "https://www.bd-pratidin.com/rss.xml"),
    ("নয়া দিগন্ত", "বাংলা সংবাদপত্র", "https://www.dailynayadiganta.com/rss.xml"),
    ("দৈনিক জনকণ্ঠ", "বাংলা সংবাদপত্র", "https://www.dailyjanakantha.com/rss"),
    ("বণিক বার্তা", "বাংলা সংবাদপত্র", "https://bonikbarta.net/rss"),
    ("দৈনিক ইনকিলাব", "বাংলা সংবাদপত্র", "https://dailyinqilab.com/rss"),
]

# Ten English-language sources, prioritising opinion/editorial and analysis.
ENGLISH_FEEDS = [
    ("The Daily Star", "English Editorials", "https://www.thedailystar.net/opinion/rss.xml"),
    ("Dhaka Tribune", "English Editorials", "https://www.dhakatribune.com/opinion/rss"),
    ("New Age", "English Editorials", "https://www.newagebd.net/rss"),
    ("The Financial Express", "English Editorials", "https://thefinancialexpress.com.bd/rss"),
    ("The Business Standard", "English Editorials", "https://www.tbsnews.net/rss.xml"),
    ("The New York Times — Opinion", "International Affairs", "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/international/section/opinion/rss.xml"),
    ("The Guardian — Opinion", "International Affairs", "https://www.theguardian.com/commentisfree/rss"),
    ("The Economist — Leaders", "International Affairs", "https://www.economist.com/leaders/rss.xml"),
    ("Financial Times — FT View", "International Affairs", "https://www.ft.com/comment/editorial?format=rss"),
    ("Project Syndicate", "International Affairs", "https://www.project-syndicate.org/rss"),
]

TOPIC_RULES = {
    "Economy & Banking": ["econom", "inflation", "bank", "banking", "fiscal", "monetary", "currency", "trade", "export", "import", "debt", "budget", "revenue", "investment", "টাকা", "ব্যাংক", "অর্থনীতি", "মূল্যস্ফীতি", "রপ্তানি", "আমদানি", "বাজেট"],
    "Governance & Public Policy": ["governance", "govern", "election", "democracy", "corruption", "policy", "reform", "parliament", "judiciary", "প্রশাসন", "নির্বাচন", "গণতন্ত্র", "দুর্নীতি", "সংস্কার", "নীতি"],
    "International Relations": ["diplomacy", "geopolit", "foreign policy", "war", "conflict", "china", "india", "united states", "russia", "middle east", "climate", "migration", "কূটনীতি", "যুদ্ধ", "আন্তর্জাতিক"],
    "Development & Society": ["poverty", "inequality", "education", "health", "employment", "gender", "development", "sustainable", "population", "দারিদ্র্য", "বৈষম্য", "শিক্ষা", "স্বাস্থ্য", "কর্মসংস্থান", "উন্নয়ন"],
    "Technology & Environment": ["artificial intelligence", "technology", "cyber", "digital", "energy", "renewable", "environment", "climate change", "বায়ুদূষণ", "জলবায়ু", "প্রযুক্তি", "জ্বালানি"],
}

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

def local_name(tag):
    return tag.split("}")[-1].lower()

def first_text(element, names):
    for child in element.iter():
        if local_name(child.tag) in names and child.text:
            return child.text
    return ""

def article_link(entry):
    for child in entry:
        if local_name(child.tag) == "link":
            href = child.attrib.get("href", "").strip()
            if href:
                return href
            if child.text and child.text.strip():
                return child.text.strip()
    return ""

def topics_for(text):
    lower = text.lower()
    return [topic for topic, words in TOPIC_RULES.items() if any(word in lower for word in words)]

def fetch_feed(source, category, url):
    req = urllib.request.Request(url, headers={"User-Agent": "EditorialHub/2.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
    entries = [e for e in root.iter() if local_name(e.tag) in ("item", "entry")]
    output = []
    for entry in entries[:35]:
        title = clean(first_text(entry, {"title"}))
        link = article_link(entry)
        summary = clean(first_text(entry, {"description", "summary", "content", "encoded"}))
        date = first_text(entry, {"pubdate", "published", "updated", "date"})
        if title and link.startswith("http"):
            topics = topics_for(title + " " + summary)
            priority = "High" if len(topics) >= 2 else ("Medium" if topics else "General")
            output.append({
                "title": title, "link": link, "summary": summary[:420],
                "date": clean(date), "source": source, "category": category,
                "topics": topics, "exam_priority": priority,
            })
    return output

articles = []
feed_status = []
for source, category, url in BANGLA_FEEDS + ENGLISH_FEEDS:
    try:
        found = fetch_feed(source, category, url)
        articles.extend(found)
        feed_status.append({"source": source, "status": "ok", "count": len(found)})
        print("OK:", source, len(found))
    except Exception as exc:
        feed_status.append({"source": source, "status": "failed", "count": 0, "error": str(exc)[:180]})
        print("Feed failed:", source, str(exc))

seen = set()
unique = []
for article in articles:
    if article["link"] not in seen:
        seen.add(article["link"])
        unique.append(article)
unique.sort(key=lambda a: a.get("date", ""), reverse=True)

with open("feed.json", "w", encoding="utf-8") as output:
    json.dump({
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "articles": unique[:250],
        "feed_status": feed_status,
        "sources_configured": {"Bangla": len(BANGLA_FEEDS), "English": len(ENGLISH_FEEDS)},
    }, output, ensure_ascii=False, indent=2)
print("Wrote", min(len(unique), 250), "articles from", sum(1 for f in feed_status if f["status"] == "ok"), "working feeds")
