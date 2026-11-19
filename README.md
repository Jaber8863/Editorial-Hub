# Editorial Hub Bangladesh

A free, open-source editorial and news RSS dashboard for Bank / IBA written-exam preparation.

## Features
- Bangladesh, International, Economy & Banking, and English Editorial categories
- Search and local bookmarks
- Automated RSS collection every four hours
- Exam-oriented essay and writing practice prompts
- Links to publishers' original articles

## Deployment
Open repository Settings, then Pages. Set Build and deployment Source to GitHub Actions once. The workflow deploys on every push and refreshes feeds every four hours.

## RSS sources
The feed list is maintained in scripts/fetch_feeds.py. Publishers retain ownership of their content; this project stores headlines, short feed excerpts, dates and links.
