# Documentation Index

This folder contains evaluator-facing technical documentation.

## Core Documents

- `AGENTS.md`
  - Agent responsibilities, routing rules, guardrails, and tool coverage.
- `CHALLENGE_READINESS.md`
  - Requirement-by-requirement mapping for the coding challenge.
- `DEPLOYMENT.md`
  - Single-VPS deployment (Docker + Nginx + Evolution API).
- `DEPLOY_VERCEL_RAILWAY_EVOLUTION.md`
  - Split deployment strategy (Vercel frontend + Railway backend + Evolution API staging).
- `PRESENTATION_QA.md`
  - Curated test scenarios with expected routes and acceptance criteria.
- `MOCK_DATA.md`
  - Seeded in-memory accounts and recommended user IDs for support demos.
- `DATABASE_STATE.md`
  - Current data layer snapshot: SQLite checkpointer, ChromaDB state, and in-memory repositories.

## Architecture Reference

- Root `architecture_review.md`
  - Full architecture review: stack, code map, runtime flow, agent graph, system context, request lifecycle, WhatsApp handoff, hardening, Docker topology, and observability entry points.
