## Context

The app has a prediction engine (statistical + ML models) that produces number suggestions under `/play`, and a separate correlation explorer under `/research` for time-series analysis. Neither feature accepts qualitative, natural-language input. Users frequently want to "play a hunch" based on lived experience (a vivid dream, a recurring nightmare, a meaningful event), but the system has no pathway to translate personal narrative into a number set.

The **dream-oracle** capability adds that pathway. Its core design challenge is: how do you convert subjective narrative into a reproducible, explainable number probability bias in a way that is structured (not just "LLM, guess 15 numbers"), transparent, and clearly labelled as entertainment?

The service already runs an Anthropic SDK agent loop with a tool-dispatch pattern (`service/src/service/agents/__init__.py`). The `materialize_suggestion` tool already converts a probability distribution into 15 numbers. This capability reuses both.

## Goals / Non-Goals

**Goals:**
- Accept a free-text dream/scenario description and return 15 suggested numbers plus a symbolic explanation.
- Make the symbol→number mapping transparent via a versioned **symbolic catalog** stored in the service.
- Reuse the existing `materialize_suggestion` pipeline so number selection is consistent with the rest of the app.
- Stream agent reasoning to the client via SSE (same pattern as `/v1/predictions/next-draw`).
- Label every response `artifact_type: entertainment` — never `prediction`.

**Non-Goals:**
- Modifying the correlation or prediction-engine capabilities.
- Persisting dream inputs or storing them for analysis (privacy).
- Claiming any statistical or causal relationship between dreams and lottery outcomes.
- Supporting languages other than Portuguese in the symbolic catalog (v1).

## Decisions

### D1 — Structured extraction before number generation, not direct LLM number selection

**Decision**: The agent MUST call `extract_dream_signals` first (a new tool that returns structured JSON: `{ symbols: [{ category, label, intensity }] }`), then build a bias vector from the catalog, then call `materialize_suggestion`. Direct "pick 15 numbers from this dream" prompting is forbidden.

**Rationale**: An unconstrained LLM picking numbers from prose is unauditable, non-reproducible, and legally/ethically harder to disclaim. The two-step approach gives every number a symbolic trail: e.g. "you dreamt of water (category: element, intensity: 0.8) → lower-range numbers 1–7 received +0.8 bias."

**Alternative considered**: Ask the LLM directly for 15 numbers with explanation — rejected because provenance would be unverifiable and results would vary across runs with the same input.

---

### D2 — Symbolic catalog as a versioned Python module, not an LLM prompt fragment

**Decision**: The catalog lives in `service/src/service/oracle/catalog.py` as a typed dict mapping `(category, label) → BiasRule`. A `BiasRule` specifies which number range or individual numbers get a probability multiplier and what the human-readable rationale is.

**Rationale**: Keeping the catalog in code means it is version-controlled, testable, and reviewable. Putting it inside the prompt makes it invisible to tests and subject to prompt-injection attacks.

**Catalog structure (v1)**:
- `element` → water(1-7), fire(19-25), earth(8-14), air(15-21), void(1,13,25)
- `color` → red(1-5), orange(6-10), yellow(11-15), green(16-20), blue(21-25)
- `emotion` → joy(even numbers), fear(odd numbers), calm(multiples of 3), rage(primes)
- `count` → explicit integers in 1-25 mentioned in the dream get a direct strong boost
- `archetype` → falling(descending sequence bias: 21-25), flying(1-5), chasing(spread/high-range), hiding(low-range 1-10)

---

### D3 — New module `service/oracle/` — not extending `agents/`

**Decision**: `service/src/service/oracle/` contains its own agent function `interpret_dream`, its own prompt, and its own tool (`extract_dream_signals`). It reuses `materialize_suggestion` from `service.tools` but does not extend or modify the prediction agent.

**Rationale**: Keeps concerns separated. The prediction agent is calibrated and complexity-budget is already at its limit. Mixing entertainment/symbolic logic into it risks degrading its statistical integrity.

---

### D4 — `artifact_type: entertainment` (new label)

**Decision**: Dream oracle results carry `artifact_type: "entertainment"`, not `"research"` or `"prediction"`. The disclaimer is distinct: *"Numbers are derived from symbolic mapping for entertainment. No statistical or predictive basis."*

**Rationale**: `"research"` implies statistical methodology. This capability is explicitly not that.

---

### D5 — Client page under `/play/dream`, not `/research`

**Decision**: The page lives under the Play section because it produces a 15-number suggestion the user might act on. Research mode is for statistical analysis.

## Risks / Trade-offs

- **[Risk] LLM ignores the two-step constraint and emits numbers directly** → Mitigation: system prompt explicitly prohibits returning numbers without a prior `extract_dream_signals` call; the agent validator checks that the tool trace contains `extract_dream_signals` before `materialize_suggestion`.
- **[Risk] Symbolic catalog is culturally biased** → Mitigation: v1 is explicitly labelled a best-effort mapping, not canonical. The catalog version is included in the response so users know what ruleset was applied.
- **[Risk] Users treat entertainment results as real predictions** → Mitigation: `artifact_type: entertainment` + prominent disclaimer + banned words linter (same as play surface: "guaranteed", "winning", "sure").
- **[Risk] Dream text contains sensitive personal content** → Mitigation: inputs are not logged or stored; the service processes them in-memory and discards after response.
- **[Risk] Prompt injection via dream text** → Mitigation: dream text is passed as a user turn in a separate message, not interpolated into the system prompt. The agent's tool-use loop is isolated from the raw text.

## Open Questions

- Should `extract_dream_signals` return a fixed maximum number of symbols (e.g. top 5 by intensity) to keep bias vectors bounded? → Proposed: yes, cap at 8 symbols per request.
- Should the catalog be user-extensible via a JSON file (like signals)? → Out of scope for v1, defer.
