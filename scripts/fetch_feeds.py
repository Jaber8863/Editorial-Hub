import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from urllib.parse import quote_plus, urlparse

def google_news_feed(domain, terms, language="en", country="BD", edition="BD:en"):
    query = f"site:{domain} {terms}"
    return "https://news.google.com/rss/search?q=" + quote_plus(query) + f"&hl={language}&gl={country}&ceid={quote_plus(edition)}"

# Only the requested exam-relevant newspaper sections are collected:
# International page, Economics/Business page, and Editorial/Opinion.
BANGLA_PAPERS = [
    ("প্রথম আলো", "prothomalo.com"), ("যুগান্তর", "jugantor.com"),
    ("কালের কণ্ঠ", "kalerkantho.com"), ("সমকাল", "samakal.com"),
    ("দৈনিক ইত্তেফাক", "ittefaq.com.bd"), ("বাংলাদেশ প্রতিদিন", "bd-pratidin.com"),
    ("নয়া দিগন্ত", "dailynayadiganta.com"), ("দৈনিক জনকণ্ঠ", "dailyjanakantha.com"),
    ("বণিক বার্তা", "bonikbarta.net"), ("দৈনিক ইনকিলাব", "dailyinqilab.com"),
]
BD_ENGLISH_PAPERS = [
    ("The Daily Star", "thedailystar.net"), ("Dhaka Tribune", "dhakatribune.com"),
    ("New Age", "newagebd.net"), ("The Financial Express", "thefinancialexpress.com.bd"),
    ("The Business Standard", "tbsnews.net"),
]

FEEDS = []
for name, domain in BANGLA_PAPERS:
    FEEDS.extend([
        (name, "Bangladesh · বাংলা", "International Page", google_news_feed(domain, '(আন্তর্জাতিক OR বিশ্ব OR পররাষ্ট্র)', "bn", "BD", "BD:bn")),
        (name, "Bangladesh · বাংলা", "Economics Page", google_news_feed(domain, '(অর্থনীতি OR অর্থ-বাণিজ্য OR ব্যাংক OR ব্যবসা OR বাজার)', "bn", "BD", "BD:bn")),
        (name, "Bangladesh · বাংলা", "Editorial / Opinion", google_news_feed(domain, '(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)', "bn", "BD", "BD:bn")),
    ])
for name, domain in BD_ENGLISH_PAPERS:
    FEEDS.extend([
        (name, "Bangladesh · English", "International Page", google_news_feed(domain, '(international OR world OR foreign affairs)', "en", "BD", "BD:en")),
        (name, "Bangladesh · English", "Economics Page", google_news_feed(domain, '(economy OR banking OR business OR finance OR markets)', "en", "BD", "BD:en")),
        (name, "Bangladesh · English", "Editorial / Opinion", google_news_feed(domain, '(editorial OR opinion OR op-ed OR analysis)', "en", "BD", "BD:en")),
    ])

# International outlets: world/international coverage and editorial/opinion only.
WORLD_FEEDS = [
    ("BBC News — World", "International", "International Page", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC News বাংলা", "International", "International Page", "https://feeds.bbci.co.uk/bengali/rss.xml"),
    ("Al Jazeera", "International", "International Page", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The New York Times", "International", "Editorial / Opinion", "https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml"),
    ("The Guardian", "International", "Editorial / Opinion", "https://www.theguardian.com/commentisfree/rss"),
    ("The Economist", "International", "Editorial / Opinion", "https://www.economist.com/leaders/rss.xml"),
    ("Deutsche Welle", "International", "International Page", "https://rss.dw.com/rdf/rss-en-all"),
    ("France 24", "International", "International Page", "https://www.france24.com/en/rss"),
    ("Project Syndicate", "International", "Editorial / Opinion", "https://www.project-syndicate.org/rss"),
    ("NPR — World", "International", "International Page", "https://feeds.npr.org/1004/rss.xml"),
]
for name, category, section, url in WORLD_FEEDS:
    FEEDS.append((name, category, section, url))

TOPIC_RULES = {
    "Economy & Banking": ["econom", "inflation", "bank", "banking", "fiscal", "monetary", "currency", "trade", "export", "import", "debt", "budget", "revenue", "investment", "টাকা", "ব্যাংক", "অর্থনীতি", "মূল্যস্ফীতি", "রপ্তানি", "আমদানি", "বাজেট"],
    "Geopolitics": ["geopolit", "diplomacy", "foreign policy", "war", "conflict", "china", "india", "united states", "russia", "middle east", "sanction", "migration", "কূটনীতি", "যুদ্ধ", "ভূরাজনীতি"],
    "Governance & Public Policy": ["governance", "govern", "election", "democracy", "corruption", "policy", "reform", "parliament", "judiciary", "প্রশাসন", "নির্বাচন", "গণতন্ত্র", "দুর্নীতি", "সংস্কার", "নীতি"],
    "International Treaties & Pacts": ["pact", "agreement", "treaty", "memorandum of understanding", "চুক্তি", "সমঝোতা"],
    "Conferences & Summits": ["conference", "summit", "forum", "সম্মেলন", "শীর্ষ সম্মেলন"],
    "Seminars & Reports": ["seminar", "workshop", "report launch", "সেমিনার", "প্রতিবেদন প্রকাশ"],
    "Prizes & Awards": ["prize", "award", "laureate", "nobel", "পুরস্কার", "সম্মাননা"],
    "Environment & Climate": ["climate", "environment", "biodiversity", "emission", "জলবায়ু", "পরিবেশ"],
    "Elections & Democracy": ["election", "poll", "vote", "নির্বাচন", "ভোট"],
    "Military & Alliances": ["military alliance", "defence pact", "defense pact", "joint exercise", "সামরিক জোট", "প্রতিরক্ষা চুক্তি"],
    "Global Rankings & Indices": ["ranking", "ranked", "index", "indices", "সূচক", "র‍্যাংকিং", "র‌্যাংকিং"],
    "Science, Technology & AI": ["artificial intelligence", "technology", "cyber", "digital", "automation", "প্রযুক্তি", "কৃত্রিম বুদ্ধিমত্তা"],
    "Society & Development": ["poverty", "inequality", "education", "health", "employment", "gender", "development", "দারিদ্র্য", "বৈষম্য", "শিক্ষা", "স্বাস্থ্য", "কর্মসংস্থান"],
}

def clean(value):
    value = unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()

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

def is_epaper(title, link):
    title_l = (title or "").lower()
    url_l = (link or "").lower()
    return bool(
        re.search(r"(e[- ]?paper|ই[- ]?পেপার|পৃষ্ঠা\s*[-–:]?\s*\d+|page\s*[-–:]?\s*\d+)", title_l)
        or re.search(r"(epaper|e-paper|pdfviewer|pageview|/epaper/)", url_l)
    )

def clean_headline(title, source):
    title = clean(title)
    # Google News appends the publisher after a final " - Publisher" suffix.
    suffixes = [source, source.replace(" ", ""), urlparse(source).netloc]
    for suffix in suffixes:
        if suffix and title.lower().endswith(" - " + suffix.lower()):
            title = title[:-(len(suffix) + 3)].strip()
    title = re.sub(r"\s+[|–—-]\s+(?:[a-z0-9-]+\.)+(?:com|net|org|bd)(?:\.[a-z]{2,})?$", "", title, flags=re.I).strip()
    return title

def topics_for(text):
    lower = text.lower()
    return [topic for topic, words in TOPIC_RULES.items() if any(word in lower for word in words)]

def fetch_feed(source, category, section, url):
    request = urllib.request.Request(url, headers={"User-Agent": "EditorialHub/3.0 (+https://jaber8863.github.io/Editorial-Hub/)"})
    root = ET.fromstring(urllib.request.urlopen(request, timeout=25).read())
    entries = [entry for entry in root.iter() if local_name(entry.tag) in ("item", "entry")]
    output = []
    for entry in entries[:45]:
        raw_title = first_text(entry, {"title"})
        link = article_link(entry)
        title = clean_headline(raw_title, source)
        summary = clean(first_text(entry, {"description", "summary", "content", "encoded"}))
        date = first_text(entry, {"pubdate", "published", "updated", "date"})
        if not title or not link.startswith("http") or is_epaper(title, link):
            continue
        topics = topics_for(title + " " + summary)
        priority = "High" if len(topics) >= 2 else ("Medium" if topics else "General")
        output.append({
            "title": title, "link": link, "summary": summary[:900],
            "date": clean(date), "source": source, "category": category,
            "section": section, "type": section, "topics": topics,
            "exam_priority": priority,
        })
    return output

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def fetch_feed_safe(feed):
    source, category, section, url = feed
    last_error = None
    for attempt in range(3):
        try:
            found = fetch_feed(source, category, section, url)
            return {"source": source, "category": category, "section": section,
                    "status": "ok", "count": len(found)}, found
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    return {"source": source, "category": category, "section": section,
            "status": "failed", "count": 0, "error": str(last_error)[:180]}, []

articles = []
feed_status = []
# Fetch feeds concurrently so one slow publisher cannot hold up the entire update.
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(fetch_feed_safe, feed) for feed in FEEDS]
    for future in as_completed(futures):
        status, found = future.result()
        feed_status.append(status)
        articles.extend(found)
        print(("OK: " if status["status"] == "ok" else "FAILED: "),
              status["source"], status["section"], status["count"],
              status.get("error", ""))

seen = set()
unique = []
for article in articles:
    key = article["link"].split("?")[0].rstrip("/")
    if key not in seen:
        seen.add(key)
        unique.append(article)
unique.sort(key=lambda article: article.get("date", ""), reverse=True)

# Always publish a valid JSON file, even when every upstream feed is temporarily unavailable.
payload = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "articles": unique[:500],
    "feed_status": sorted(feed_status, key=lambda x: (x["status"] != "ok", x["source"], x["section"])),
    "sources_configured": {
        "Bangla newspapers": len(BANGLA_PAPERS),
        "Bangladesh English newspapers": len(BD_ENGLISH_PAPERS),
        "International outlets": len(WORLD_FEEDS),
        "sections_per_Bangladesh_paper": ["International Page", "Economics Page", "Editorial / Opinion"],
    },
    "health": {
        "configured_feeds": len(FEEDS),
        "working_feeds": sum(1 for feed in feed_status if feed["status"] == "ok"),
        "failed_feeds": sum(1 for feed in feed_status if feed["status"] != "ok"),
        "article_count": len(unique),
    },
}
with open("feed.json", "w", encoding="utf-8") as output:
    json.dump(payload, output, ensure_ascii=False, indent=2)
print("Wrote", min(len(unique), 500), "articles from",
      payload["health"]["working_feeds"], "of", len(FEEDS), "working feeds")
