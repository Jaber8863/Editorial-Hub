# Editorial Hub — AI Article Study Backend

## Required hosting
GitHub Pages is static hosting and cannot execute the `api/study.js` serverless function. Deploy this repository on Vercel (import the GitHub repo `Jaber8863/Editorial-Hub`).

## Environment variables (Vercel Project → Settings → Environment Variables)
- `OPENAI_API_KEY`: secret OpenAI API key. Never put it in `index.html`, feed.json, or client-side code.
- `OPENAI_MODEL` (optional): defaults to `gpt-4.1-mini`.

After adding the secret, redeploy.

## How it works
1. The page sends an article URL/title/feed summary to `POST /api/study`.
2. The server validates the article URL and retrieves its full text using the reader service.
3. If full text cannot be extracted (blocked/paywall/too short), the API returns an error and does not generate an article-based essay.
4. It sends the extracted article text to OpenAI, asking for structured, article-grounded IBA/Bangladesh Bank preparation: summaries, facts, analysis, Bangladesh angle, probable questions, focus writing in both languages, vocabulary, translation, grammar, practice.
5. The result is cached in the user's browser. The “AI Analyze all visible articles” button queues the visible articles sequentially.

## Cost & safeguards
- Each article analysis makes an article-reader request and an OpenAI API request, so it may incur API charges.
- API key is server-side only.
- Endpoint only accepts HTTPS and a set of known news domains/Google News article links.
- Basic per-instance rate limit is included (not a substitute for a persistent production rate limiter).
- The frontend cache can be refreshed article-by-article.
- Verify facts/figures with the original article before using in exam writing.
