import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone\nfrom urllib.parse import quote_plus

def google_news_feed(domain, terms, language="en", country="US", edition="US:en"):
    query = f"site:{domain} {terms}"
    return "https://news.google.com/rss/search?q=" + quote_plus(query) + f"&hl={language}&gl={country}&ceid={quote_plus(edition)}"

# Ten major Bangla newspapers. Google News RSS search is used where publishers
# block direct RSS or do not expose a stable public editorial feed.
BANGLA_FEEDS = [
    ("প্রথম আলো", "বাংলা সংবাদপত্র", google_news_feed("prothomalo.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("যুগান্তর", "বাংলা সংবাদপত্র", google_news_feed("jugantor.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("কালের কণ্ঠ", "বাংলা সংবাদপত্র", google_news_feed("kalerkantho.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("সমকাল", "বাংলা সংবাদপত্র", google_news_feed("samakal.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("দৈনিক ইত্তেফাক", "বাংলা সংবাদপত্র", google_news_feed("ittefaq.com.bd", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("বাংলাদেশ প্রতিদিন", "বাংলা সংবাদপত্র", google_news_feed("bd-pratidin.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("নয়া দিগন্ত", "বাংলা সংবাদপত্র", google_news_feed("dailynayadiganta.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("দৈনিক জনকণ্ঠ", "বাংলা সংবাদপত্র", google_news_feed("dailyjanakantha.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("বণিক বার্তা", "বাংলা সংবাদপত্র", google_news_feed("bonikbarta.net", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
    ("দৈনিক ইনকিলাব", "বাংলা সংবাদপত্র", google_news_feed("dailyinqilab.com", "(সম্পাদকীয় OR মতামত OR উপসম্পাদকীয়)", "bn", "BD", "BD:bn")),
]

# Five Bangladesh-based English-language newspapers and business publications.
BD_ENGLISH_FEEDS = [
    ("The Daily Star", "Bangladesh English", google_news_feed("thedailystar.net", "(opinion OR editorial OR analysis)", "en", "BD", "BD:en")),
    ("Dhaka Tribune", "Bangladesh English", google_news_feed("dhakatribune.com", "(opinion OR editorial OR analysis)", "en", "BD", "BD:en")),
    ("New Age", "Bangladesh English", google_news_feed("newagebd.net", "(opinion OR editorial OR analysis)", "en", "BD", "BD:en")),
    ("The Financial Express", "Bangladesh English", google_news_feed("thefinancialexpress.com.bd", "(opinion OR editorial OR analysis)", "en", "BD", "BD:en")),
    ("The Business Standard", "Bangladesh English", google_news_feed("tbsnews.net", "(opinion OR editorial OR analysis)", "en", "BD", "BD:en")),
]

# Ten international sources for global affairs, editorials and analysis.
WORLD_FEEDS = [
    ("BBC News English — World", "World Analysis & Opinion", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("BBC News বাংলা", "World Analysis & Opinion", "https://feeds.bbci.co.uk/bengali/rss.xml"),
    ("Al Jazeera English", "World Analysis & Opinion", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("The New York Times — Opinion", "World Analysis & Opinion", "https://rss.nytimes.com/services/xml/rss/nyt/Opinion.xml"),
    ("The Guardian — Opinion", "World Analysis & Opinion", "https://www.theguardian.com/commentisfree/rss"),
    ("The Economist — Leaders", "World Analysis & Opinion", "https://www.economist.com/leaders/rss.xml"),
    ("Deutsche Welle — English", "World Analysis & Opinion", "https://rss.dw.com/rdf/rss-en-all"),
    ("France 24 — English", "World Analysis & Opinion", "https://www.france24.com/en/rss"),
    ("Project Syndicate", "World Analysis & Opinion", "https://www.project-syndicate.org/rss"),
    ("NPR — World", "World Analysis & Opinion", "https://feeds.npr.org/1004/rss.xml"),
]

TOPIC_RULES = {
    "Economy & Banking": ["econom", "inflation", "bank", "banking", "fiscal", "monetary", "currency", "trade", "export", "import", "debt", "budget", "revenue", "investment", "টাকা", "ব্যাংক", "অর্থনীতি", "মূল্যস্ফীতি", "রপ্তানি", "আমদানি", "বাজেট"],
    "Governance & Public Policy": ["governance", "govern", "election", "democracy", "corruption", "policy", "reform", "parliament", "judiciary", "প্রশাসন", "নির্বাচন", "গণতন্ত্র", "দুর্নীতি", "সংস্কার", "নীতি"],
    "International Relations": ["diplomacy", "geopolit", "foreign policy", "war", "conflict", "china", "india", "united states", "russia", "middle east", "sanction", "migration", "কূটনীতি", "যুদ্ধ", "আন্তর্জাতিক"],
    "Development & Society": ["poverty", "inequality", "education", "health", "employment", "gender", "development", "sustainable", "population", "দারিদ্র্য", "বৈষম্য", "শিক্ষা", "স্বাস্থ্য", "কর্মসংস্থান", "উন্নয়ন"],
    "Technology & Environment": ["artificial intelligence", "technology", "cyber", "digital", "energy", "renewable", "environment", "climate change", "বায়ুদূষণ", "জলবায়ু", "প্রযুক্তি", "জ্বালানি"],
}

def clean(s):
    return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

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
    request = urllib.request.Request(url, headers={"User-Agent": "EditorialHub/2.1"})
    root = ET.fromstring(urllib.request.urlopen(request, timeout=20).read())
    entries = [entry for entry in root.iter() if local_name(entry.tag) in ("item", "entry")]
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
all_feeds = BANGLA_FEEDS + BD_ENGLISH_FEEDS + WORLD_FEEDS
for source, category, url in all_feeds:
    try:
        found = fetch_feed(source, category, url)
        articles.extend(found)
        feed_status.append({"source": source, "category": category, "status": "ok", "count": len(found)})
        print("OK:", source, len(found))
    except Exception as exc:
        feed_status.append({"source": source, "category": category, "status": "failed", "count": 0, "error": str(exc)[:180]})
        print("Feed failed:", source, str(exc))

seen = set()
unique = []
for article in articles:
    if article["link"] not in seen:
        seen.add(article["link"])
        unique.append(article)
unique.sort(key=lambda article: article.get("date", ""), reverse=True)

with open("feed.json", "w", encoding="utf-8") as output:
    json.dump({
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "articles": unique[:300],
        "feed_status": feed_status,
        "sources_configured": {
            "Bangla newspapers": len(BANGLA_FEEDS),
            "Bangladesh English": len(BD_ENGLISH_FEEDS),
            "International": len(WORLD_FEEDS),
        },
    }, output, ensure_ascii=False, indent=2)
print("Wrote", min(len(unique), 300), "articles from", sum(1 for feed in feed_status if feed["status"] == "ok"), "working feeds")
