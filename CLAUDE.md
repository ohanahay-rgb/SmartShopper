# SmartShopper -- AI Product Comparison & Logistics System

## What This Project Does
Israeli product comparison: receives search via Telegram, scrapes 15+
Israeli e-commerce sites, shows 5 best options with shipping costs
(Shilichuyot delivery company).

## Architecture
- **Agent Framework:** LangGraph StateGraph + langgraph-supervisor
- **Agent Pattern:** create_supervisor() with create_react_agent() workers
  (from langgraph-supervisor-py)
- **Telegram:** Aiogram v3 + FastAPI webhooks with dp.feed_webhook_update()
  (from tg-bot-fastapi-aiogram)
- **Scraping:** Scrapy + Playwright
- **Database:** PostgreSQL 16 + Redis 7
- **Config:** Pydantic BaseSettings with nested settings + @lru_cache

## Business Rules (NEVER CHANGE)
- Always return exactly 5 results
- Each result: product_price + shipping_cost = total
- Shipping formula: (50 + distance_km * 3) * size_factor
- Size factors: S=1.0, M=1.5, L=2.5, XL=4.0
- Round shipping cost to whole ILS
- Two buttons per result: "Direct Purchase" + "Order Delivery"
- Daily report at 23:00 Israel time (Asia/Jerusalem)
- Report includes: search count, popular products, conversion rate
- Delivery partner: Shilichuyot Ltd (fixed, not replaceable)
- Scrape at least 15 sites per search

## Agent Hierarchy
- Supervisor (Claude Opus 4.6): intent parsing, quality validation
- Orchestrator (GPT-4o mini): task routing to workers
- Search Agent: Scrapy + Playwright scraping
- Price Analysis Agent: rule-based, no LLM
- Logistics Agent: Google Maps + shipping formula, no LLM
- Recommendation Agent (GPT-4o mini): rank + pick top 5
- Telegram Interface Agent: Aiogram, no LLM
- Report Agent (GPT-4o mini): daily reports
- Monitoring Agent: health, budget, circuit breakers, no LLM

## Commands
- `docker compose up` -- start all services
- `docker compose up postgres redis` -- DB + cache only
- `pytest` -- run all tests
- `alembic upgrade head` -- run DB migrations
- `python scripts/simulate_request.py` -- test a search

## Tech Decisions (Free to optimize)
- Internal code structure and variable names
- Error messages to users
- Number of concurrent scraping requests
- Cache TTL values
- Test organization and edge cases
- Retry counts and backoff strategies
