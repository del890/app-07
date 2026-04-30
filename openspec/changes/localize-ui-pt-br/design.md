## Context

The Lotofácil webapp is a Nuxt 3 + TypeScript SPA targeting Brazilian lottery players and researchers. All user-facing strings are currently hardcoded in English directly inside `.vue` template and `<script setup>` blocks across 17+ files. There is no existing i18n framework or locale abstraction layer.

## Goals / Non-Goals

**Goals:**
- Replace all English UI strings in `client/app/` with accurate Portuguese (pt-BR) equivalents
- Cover pages, layouts, components, and inline `useHead` / error strings
- Keep the change purely cosmetic — no behavioral or structural code changes

**Non-Goals:**
- Introducing an i18n framework (e.g., `@nuxtjs/i18n`, `vue-i18n`) — not needed for a single-locale app
- Translating code comments, variable names, or type identifiers
- Translating backend/service messages (API error payloads, log messages)
- Supporting multiple languages or a locale-switching mechanism

## Decisions

### Direct inline replacement, no i18n library

**Decision:** Replace hardcoded English strings in-place inside each `.vue` file. No locale extraction to external JSON/YAML files.

**Rationale:** The app serves a single locale. Extracting strings to a locale file adds tooling overhead (install, configure, wrap every string with `$t()`), increases bundle complexity, and provides no practical benefit when only one language will ever be used. Direct replacement is simpler, reviewable diff-by-diff, and fully reversible.

**Alternatives considered:**
- `@nuxtjs/i18n` with a `pt-BR.json` file — rejected; over-engineered for a single-locale product.
- A shared composable `useTexts()` that returns a constant object — rejected; adds indirection without benefit.

### Scope: template strings only (no data-layer translation)

Research labels sourced from the API (e.g., statistic keys returned as JSON) are not in scope. Only strings that are authored in `.vue` files will be translated.

## Risks / Trade-offs

- **Partial translation risk** → Mitigation: tasks enumerate every file explicitly; each task covers one file completely to avoid missed strings.
- **Inconsistent terminology** → Mitigation: specs define a canonical glossary (e.g., "Sorteio" for Draw, "Previsão" for Prediction) applied uniformly.
- **Regression in text rendered by child components** → Mitigation: component-level tasks are separate and reviewed against their parent page context.

## Migration Plan

1. Translate files in dependency order: layout → shared components → pages
2. Verify visually in dev server after each major file group
3. No rollback strategy required beyond `git revert` — purely cosmetic change with no data migration
