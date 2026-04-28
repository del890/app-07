## Why

The Play section's "Suggest Next Draw" experience is functional but visually crude: the loading phase is a plain text label ("Analysing…"), the streamed tool events render as raw `font-mono` rows, and the final prediction card is a minimal unstyled block. Upgrading these to polished, modern UI patterns will make the tool feel professional and give the user meaningful progress feedback while the agent works.

## What Changes

- **Loading / streaming phase**: Replace the plain text button label + raw event log with an animated progress timeline that shows each tool call as a step with a status icon (running / done), a human-readable label, and a subtle pulse animation while active.
- **Prediction result card** ("Suggest Next Draw"): Replace the flat card with an engaging layout — a large number grid with staggered entrance animation, a prominent confidence meter, and the explanation displayed with better typography.
- **Scenario Path steps**: Apply the same design language to each path step — numbered step indicator, animated number reveal, and inline confidence meter per step.
- **Shared `PredictionCard` component**: Extract the common "numbers + confidence + explanation" layout into a reusable component used by both pages.
- **Shared `ToolProgressTimeline` component**: Extract the streaming tool-event log into a dedicated timeline component consumed by both pages.

## Capabilities

### New Capabilities

- `play-loading-experience`: Animated streaming-progress timeline component (`ToolProgressTimeline.vue`) that visualises running / completed agent tool calls during SSE streaming.
- `play-result-presentation`: Polished prediction result components — `PredictionCard.vue` for single-draw results and updated scenario step cards — with entrance animations, confidence meter, and improved typography.

### Modified Capabilities

*(none — no existing spec-level requirements change; this is purely a presentation upgrade)*

## Impact

- **New files**: `client/app/components/ToolProgressTimeline.vue`, `client/app/components/PredictionCard.vue`
- **Modified files**: `client/app/pages/play/next-draw.vue`, `client/app/pages/play/scenario.vue`
- **No service changes. No new npm dependencies required** (Tailwind CSS animation utilities are already available).
