# Creative Performance & Production Prioritization Agent
Railway-ready Streamlit MVP for a UA creative production assessment.

## Function
- Upload campaign CSV.
- Calculate CTR, CVR, CPI and ROAS if revenue is supplied.
- Flag simple data-quality issues.
- Optionally use an OpenAI model to produce evidence-based creative test priorities.
- Export analyzed CSV, recommendation.md and execution_log.md.

## Deploy to Railway
1. Upload these files to a GitHub repository.
2. Railway: New Project → Deploy from GitHub Repo.
3. Add Variables to the Railway service: OPENAI_API_KEY and optionally OPENAI_MODEL (default gpt-4.1-mini).
4. Deploy and open the generated URL.
5. Upload the CSV from the live exercise.

Never commit API keys to GitHub. Do not upload confidential campaign data to an unapproved third-party model.

## CSV columns
Required: spend, impressions, clicks, installs.
Optional: creative, format, hook, duration_sec, audience, country, revenue.
Some aliases are normalized (e.g. cost → spend; impr → impressions; app_installs → installs).

## Local run
pip install -r requirements.txt
streamlit run app.py

## Assessment note
The sample CSV is fictional and should only be used to smoke-test the app. During the assessment, use the provided dataset. This MVP is decision support, not autonomous budget/creative approval. Validate recommendations and retain human review for brand/IP, legal, localization and budget.
