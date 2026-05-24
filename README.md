# Opptra — Pricing Intelligence

Opptra is a compact pricing-intelligence prototype that combines rule-based logic, lightweight storage, and multiple large language models to generate, synthesize, and review per-SKU pricing recommendations.

Key ideas
- Purpose: provide explainable, reviewable SKU pricing recommendations and cluster-level insights so a pricing analyst can accept, override, or snooze AI suggestions.
- Architecture: thin FastAPI backend that runs the AI orchestration and serves a static Next.js frontend. Data is stored in a small SQLite file for the prototype.
- AI-first, but resilient: primary model is Anthropic Claude Sonnet (when available); the system falls back to OpenAI GPT-4o, and optionally to Grok (XAI) before using a deterministic fallback.

Highlights
- Recommendation pipeline (per SKU): feature extraction → LLM scoring → post-processing gates → deterministic fallback when all LLMs fail.
- Clustering & synthesis: combines SKU recommendations into human-reviewable clusters and short-form portfolio insights.
- UI: queue-based workflow for reviewing clusters and per-SKU decisions, with quick actions (approve/snooze/override) and reasoning visibility.

Model mapping
- Primary: Anthropic Claude Sonnet 4 (recommendations, clustering)
- Fallback 1: OpenAI GPT-4o (structured output / JSON parsing)
- Fallback 2 (optional): Grok via XAI-compatible API
- Overrides: Claude Haiku 3.5 (override insight generation)
- Synthesis: Google Gemini 1.5 Pro (portfolio-level synthesis)

Data and configuration
- Example environment variables: see `.env.example` in the repo root.
- Seed data and test fixtures are under `data/` and `backend/tests/fixtures`.
