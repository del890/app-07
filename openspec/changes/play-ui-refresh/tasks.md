## 1. ToolProgressTimeline Component

- [x] 1.1 Create `client/app/components/ToolProgressTimeline.vue` accepting `:events="SseEvent[]"` prop
- [x] 1.2 Implement internal tool-name humanisation map (snake_case → readable label, with title-case fallback for unknown names)
- [x] 1.3 Derive step list from `tool_start` / `tool_result` event pairs: each step has `toolName`, `label`, and `state: 'running' | 'done'`
- [x] 1.4 Render each step with its visual state: pulsing animated ring for `running`, green checkmark for `done`
- [x] 1.5 Wrap the list in `<TransitionGroup>` with a fade-in entrance so new steps animate in as events arrive
- [x] 1.6 Hide the component entirely (`v-if`) when no tool events exist

## 2. PredictionCard Component

- [x] 2.1 Create `client/app/components/PredictionCard.vue` with props: `numbers: number[]`, `confidence: number`, `explanation: string`, `provenance: PredictionProvenance`, `label?: string`
- [x] 2.2 Render the 15 number bubbles inside a `<TransitionGroup name="numbers">` with `appear` so they animate on mount
- [x] 2.3 Apply per-bubble CSS `transitionDelay` of `i * 30ms` for the staggered entrance (fade + scale from 80 % to 100 %)
- [x] 2.4 Add a horizontal confidence meter bar: width = `confidence * 100%`, colour class matching ConfidenceBadge thresholds (green ≥ 0.7, yellow ≥ 0.4, red < 0.4)
- [x] 2.5 Render `explanation` in a `max-w-prose` container with `text-base leading-relaxed`
- [x] 2.6 Render the provenance footer (dataset hash + timestamp) in small muted text; omit if `label` is set (scenario step cards skip provenance)
- [x] 2.7 Add the `<style scoped>` block defining `.numbers-enter-active`, `.numbers-enter-from` CSS transition classes

## 3. Generate Button Spinner

- [x] 3.1 In `next-draw.vue`, replace the text-only disabled state with a spinner SVG icon + label side-by-side when `isStreaming` is true
- [x] 3.2 In `scenario.vue`, apply the same spinner pattern to the Generate Scenario button

## 4. Wire ToolProgressTimeline into Play Pages

- [x] 4.1 Replace the existing raw `toolEvents` div list in `next-draw.vue` with `<ToolProgressTimeline :events="events" />`
- [x] 4.2 Add `<ToolProgressTimeline :events="events" />` to `scenario.vue` (currently has no tool-event UI at all)

## 5. Wire PredictionCard into Play Pages

- [x] 5.1 Replace the inline prediction result block in `next-draw.vue` with `<PredictionCard :numbers="..." :confidence="..." :explanation="..." :provenance="..." />`
- [x] 5.2 In `scenario.vue`, replace each inline step card with `<PredictionCard :label="\`Draw +\${step.step}\`" :numbers="..." :confidence="..." :explanation="..." :provenance="..." />`; skip the provenance footer for step cards (pass `label` prop to suppress it)
