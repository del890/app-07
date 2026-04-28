## Context

The client is Nuxt 3 + TypeScript + Tailwind CSS. The two Play pages (`next-draw.vue`, `scenario.vue`) both use `useSsePrediction()` to stream agent tool-call events and then a final prediction result. Currently:

- Streaming state: a disabled button with text "Analysing…" plus a list of `<div>` rows with raw tool names in `font-mono`.
- Result state: a flat white card with a `flex-wrap` bubble grid, a `<p>` explanation, and a tiny provenance footer.

No shared components exist between the two pages. Tailwind's `animate-pulse` and `animate-spin` utilities are available. No Vue transition API is yet used in the play section.

## Goals / Non-Goals

**Goals:**
- Animated streaming timeline: each tool call is a labelled step with visual state (pending dimmed, running pulsed ring, done checkmark).
- Polished prediction card: staggered number bubbles, explicit confidence meter bar, readable explanation block.
- Two reusable components (`ToolProgressTimeline`, `PredictionCard`) consumed by both pages.
- Zero new npm dependencies — Tailwind utilities only.

**Non-Goals:**
- Redesigning the Play index page or History page.
- Changing any service behaviour or SSE protocol.
- Adding new data — only the presentation of existing data changes.

## Decisions

### D1 — Pure Tailwind, no animation library

**Decision**: Use Tailwind's built-in `animate-pulse`, `animate-spin`, `transition-all`, and Vue's `<Transition>` / `<TransitionGroup>` for all animations.

**Alternatives considered**:
- *Auto-animate / GSAP*: Powerful but adds bundle weight for minimal gain here.
- *Headless UI Transition*: Already available in Nuxt ecosystem, but `<TransitionGroup>` from Vue core is sufficient.

**Rationale**: Zero dependencies is the ruling constraint from the proposal.

---

### D2 — `ToolProgressTimeline.vue` receives the raw `SseEvent[]` array as a prop

**Decision**: The component accepts `:events="events"` (full `SseEvent[]`), filters to `tool_start` / `tool_result` internally, and derives its display state from event pairs.

**Rationale**: Keeps the parent page free of display logic. The composable already exposes `events` — no extra wiring needed.

**Tool name humanisation**: A static lookup map inside the component converts snake_case tool names (e.g., `fetch_frequency_statistics`) to readable labels (e.g., "Frequency statistics"). Unmapped names fall back to title-cased snake_case.

---

### D3 — `PredictionCard.vue` is a dumb display component

**Decision**: Props: `numbers: number[]`, `confidence: number`, `explanation: string`, `provenance: PredictionProvenance`, optional `label?: string` (e.g., "Draw +2" for scenario steps). No internal async logic.

**Rationale**: Keeps the card reusable and testable in isolation. Both `next-draw.vue` and scenario step iteration pass data in.

---

### D4 — Staggered number entrance via `<TransitionGroup>` + CSS delay

**Decision**: Each number bubble in `PredictionCard` is wrapped in a `<TransitionGroup name="numbers">` with an `:style="{ transitionDelay: \`${i * 30}ms\` }"` per item to produce a staggered left-to-right reveal on mount.

**Rationale**: Pure CSS transition delay — no JavaScript animation ticker, zero runtime cost.

---

### D5 — Confidence meter is a filled bar, not just the `ConfidenceBadge` pill

**Decision**: `PredictionCard` renders a horizontal progress bar (width = `confidence * 100%`) in addition to the existing `ConfidenceBadge` pill. The bar uses the same green/yellow/red colour logic.

**Rationale**: A bar conveys magnitude more intuitively than a percentage badge alone.

## Risks / Trade-offs

- **`<TransitionGroup>` SSR flash**: On the server, items render without entrance classes. Mitigation: `appear` prop is set so animations still fire on client hydration.
- **Tool name map maintenance**: New tools added to the service won't have friendly labels until the map is updated. Mitigation: the fallback (title-cased snake_case) is always human-readable.
- **Scenario page coupling**: `scenario.vue` passes each `step` to `PredictionCard` via `v-for` — if the step shape changes on the service, both the page and the card are affected. Mitigation: the card takes primitive props, so only the parent page's mapping code would change.
