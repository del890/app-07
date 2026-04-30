## 1. Explanation Normalization Utility

- [x] 1.1 Add a client-side explanation normalizer utility/composable that accepts raw explanation input and returns a typed normalized model
- [x] 1.2 Implement support for three input shapes: plain text, valid JSON string, and object-like JSON content
- [x] 1.3 Add defensive parsing rules and fallback output for malformed or partially populated explanation payloads

## 2. Structured Explanation UI

- [x] 2.1 Replace raw explanation JSON rendering in prediction result card(s) with a sectioned layout (summary, highlights, top probabilities, provenance)
- [x] 2.2 Add conditional rendering so empty optional sections are omitted cleanly without placeholder gaps
- [x] 2.3 Ensure typography and spacing are readable on mobile and desktop while keeping existing card shell and confidence elements

## 3. Integrate Across Play Surfaces

- [x] 3.1 Wire the shared explanation normalizer and renderer into next-draw prediction results
- [x] 3.2 Wire the same behavior into scenario-step prediction cards to keep rendering consistent
- [x] 3.3 Verify that parse failures still produce a stable, user-friendly fallback explanation on both surfaces

## 4. Validation and Regression Checks

- [x] 4.1 Add or update client tests for normalization and fallback behavior using representative payload fixtures
- [x] 4.2 Run client lint/tests and fix regressions related to prediction explanation rendering
- [ ] 4.3 Manually verify the UI with a payload containing nested explanation highlights to confirm improved readability
