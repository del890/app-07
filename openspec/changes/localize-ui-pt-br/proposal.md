## Why

The Lotofácil webapp targets Brazilian users, but all UI texts — labels, headings, navigation, error messages, and button captions — are written in English. Translating the interface to Portuguese (pt-BR) makes the product natural and accessible for its intended audience.

## What Changes

- Replace all hardcoded English strings in pages, components, and layouts with Portuguese (pt-BR) equivalents
- Translate navigation labels, page titles, section headings, button labels, and error/status messages
- Translate research page navigation labels and descriptions (Frequency, Gaps, Co-occurrence, Structural, Draw Order, PI Alignment, Signal Correlations)
- Translate play section UI texts (scenario, next draw, my draw, scan, history)
- Translate admin page labels and status messages
- Translate component-level texts in `ConfidenceBadge`, `DrawSelector`, `PredictionCard`, `TicketScanner`, and `ToolProgressTimeline`
- Update `<title>` and `useHead` page titles to Portuguese

## Capabilities

### New Capabilities

- `ui-texts-pt-br`: Defines the complete Portuguese (pt-BR) text inventory for all UI-facing strings across pages, layouts, and components — without introducing an i18n framework. Strings are replaced inline; no locale file abstraction is required.

### Modified Capabilities

## Impact

- All `.vue` files under `client/app/pages/`, `client/app/layouts/`, and `client/app/components/`
- No API, service, or data-layer changes
- No new dependencies required
