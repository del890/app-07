## Why

The current UI relies on a heavy dark-gradient header, generic card-box layouts, and desktop-first spacing that produces a cramped, inconsistent experience on small screens. A reference design (`_process/index.html`) demonstrates a cleaner, editorial aesthetic — monospace labels, ink-on-paper tones, transparent panels, and tight mobile breakpoints — that better suits a data-heavy research tool used on the go.

## What Changes

- Replace the dark navy gradient header with a clean sticky header matching the reference style (paper background, monospace title, minimal border)
- Rework CSS design tokens (background, foreground, primary, muted, border) to reflect an ink-on-paper palette
- Introduce a monospace type treatment for section labels, badges, and metadata readouts (Roboto Mono or system monospace)
- Remove heavy card-box borders/shadows in favour of borderless or lightly-ruled panels
- Tighten mobile breakpoints across all pages: narrower horizontal padding, stacked layouts, larger tap targets (≥ 44 px)
- Redesign the bottom navigation / mode switcher for mobile (sticky bottom bar or collapsible header nav)
- Ensure lottery number badges, confidence badges, and prediction cards are finger-friendly and readable at 360 px viewport width
- Refresh button styles to match reference: filled (ink on paper) and ghost variants with monospace uppercase labels

## Capabilities

### New Capabilities
- `app-shell`: Sticky header, optional bottom nav bar, and global layout tokens (padding, max-width, z-index ladder) — the frame every page sits inside
- `design-tokens`: CSS custom properties palette (paper, ink, muted-rule, accent, success, warning) and typography scale (monospace labels, body, numeric readouts)
- `mobile-navigation`: Mobile-optimised nav pattern — collapsible or sticky bottom tab bar for Research / Play mode switching

### Modified Capabilities
- `lotofacil-prediction-webapp`: Visual presentation layer requirements updated — number badges must be ≥ 40 px on mobile, confidence badges use new token colors, prediction cards use borderless panel style

## Impact

- `client/app/assets/css/main.css` — design token overhaul
- `client/app/layouts/default.vue` — header + nav restructure
- `client/app/pages/**/*.vue` — padding, spacing, and component class adjustments across all pages
- `client/app/components/*.vue` — PredictionCard, ConfidenceBadge, DrawSelector, TicketScanner visual updates
- `client/nuxt.config.ts` — add Roboto Mono font import (Google Fonts)
- No API or service-layer changes; pure presentation
