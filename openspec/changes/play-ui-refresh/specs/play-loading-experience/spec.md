## ADDED Requirements

### Requirement: Streaming tool calls render as a progress timeline
While the SSE stream is active, the Play pages SHALL render a `ToolProgressTimeline` component that lists each agent tool call as a labelled step. Steps MUST show one of three visual states: **running** (animated pulse ring), **done** (green checkmark), or **pending** (dimmed).

#### Scenario: Tool start event shows running state
- **WHEN** a `tool_start` SSE event arrives for tool `fetch_frequency_statistics`
- **THEN** the timeline renders a new step labelled "Frequency statistics" with a pulsing animated ring indicator

#### Scenario: Tool result event marks step done
- **WHEN** a `tool_result` SSE event arrives for a tool that previously had a `tool_start` event
- **THEN** the corresponding timeline step transitions to the done state with a green checkmark

#### Scenario: Unknown tool names fall back gracefully
- **WHEN** a `tool_start` event arrives for a tool name not in the humanisation map
- **THEN** the step label displays the tool name formatted as title-cased words (snake_case converted)

#### Scenario: Timeline is hidden when there are no events
- **WHEN** no tool events have arrived yet or status is `idle`
- **THEN** the timeline is not rendered in the DOM

#### Scenario: Timeline persists after streaming completes
- **WHEN** the stream ends and status transitions to `done`
- **THEN** all steps remain visible in their final `done` state

---

### Requirement: Generate button conveys active state without text mutation
While streaming is in progress, the Generate button SHALL be disabled and display a spinner icon alongside the button label, rather than replacing the label with a different string.

#### Scenario: Spinner visible during streaming
- **WHEN** `status` is `streaming`
- **THEN** the Generate button is disabled and shows a rotating spinner icon before the label

#### Scenario: Button restores to normal on completion
- **WHEN** `status` transitions to `done` or `error`
- **THEN** the Generate button is re-enabled and the spinner is removed
