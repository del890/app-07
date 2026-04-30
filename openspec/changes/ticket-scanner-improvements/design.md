## Context

The existing scanner sends the user's ticket photo to Claude Vision with a generic prompt that describes the 5×25 grid structure in prose. The prompt does not encode the exact fixed position-to-number mapping, which means Claude must both locate the grid AND read the digits — but the digits are obscured by heavy ink marks. In practice the model sometimes fails to match cells to numbers, returning incomplete or incorrect arrays.

There are three layers of the problem:

1. **Prompt ambiguity** — the model doesn't know that cell (row=3, col=2) is always number 17.
2. **Image quality** — a raw JPEG from a hand-held phone over a paper ticket under uncontrolled lighting has low contrast between ink mark and paper.
3. **No spatial reference** — without a known-good blank ticket in the same call, the model has nothing to diff against.

The ticket layout is fully deterministic. Numbers 01–25 are placed in a 5-row × 5-column grid. The columns run right-to-left (from the player's perspective, the number 01 is in the top-right cell and 25 is in the bottom-left cell):

```
Row\Col  C1   C2   C3   C4   C5
Row 1    21   16   11   06   01
Row 2    22   17   12   07   02
Row 3    23   18   13   08   03
Row 4    24   19   14   09   04
Row 5    25   20   15   10   05
```

This fixed mapping is the single most useful piece of knowledge to put into the prompt.

## Goals / Non-Goals

**Goals:**
- Rewrite the vision prompt with an explicit cell → number mapping table so Claude reasons about position, not digit reading.
- Attach the blank reference ticket image to the Claude call so the model can visually compare filled vs. blank cells.
- Preprocess the captured image on the client (contrast boost + grayscale) before upload.
- Add a ticket alignment guide overlay in the scanner UI to reduce skewed/partial captures.
- Raise the client capture resolution cap to 1920 px.

**Non-Goals:**
- On-device CV (OpenCV, WASM) — continues to be excluded; no new dependencies.
- Changing the response schema or API surface — `ScannedTicket` is unchanged.
- Detecting ticket metadata (Surpresinha, Teimosinha, etc.).

## Decisions

### 1. Position-map prompt instead of prose description

**Choice**: Replace the prose description with an explicit ASCII table that maps every (row, col) coordinate to its number. Instruct Claude to scan each cell position and report the number at that position if it is marked, rather than trying to read the digit.

**Alternatives considered**:
- *Keep current prose + hope model orientation improves*: No deterministic benefit; the fundamental confusion between digit reading and cell detection remains.
- *Send a labelled grid image pre-computed on the server*: Adds image-generation code and complexity with little advantage over the text table.

**Rationale**: The mapping is small (25 entries), fits in a few prompt tokens, and eliminates all ambiguity about what number belongs where. This is the highest-leverage single change.

### 2. Reference blank ticket as a second image block in the Claude call

**Choice**: Read `_process/lotofacil-bilhete.webp` once at service startup, encode it as base64, and include it as the first image block in the user message. The user's photo becomes the second image block. The prompt instructs Claude: "Image 1 is the blank template; Image 2 is the filled ticket. Identify cells that appear different between the two images."

**Alternatives considered**:
- *Always-embed without startup caching*: Reading from disk per request adds I/O latency. Caching at module load is negligible memory (~50 KB).
- *Skip the reference image, rely only on the better prompt*: Weaker fallback; retaining both gives layered confidence.

**Rationale**: Visual diffing between a known blank and the user's photo is a strong cue that works even under poor lighting. Claude Vision handles two-image prompts well.

### 3. Client-side contrast preprocessing via Canvas API

**Choice**: After capturing the frame, apply a contrast filter using the Canvas 2D API's `filter` property (`contrast(180%) brightness(110%)`) before encoding the JPEG, then convert to grayscale by desaturating (`saturate(0%)`). No external library is required.

**Alternatives considered**:
- *Manual pixel manipulation*: More control (histogram equalization, adaptive thresholding) but significantly more code.
- *Server-side preprocessing with Pillow*: Would work but adds a Python dependency and processing time before the LLM call.

**Rationale**: The Canvas `filter` approach is two lines of code, zero dependencies, and runs in the browser where the image originates. The goal is modest: push ink marks to near-black and paper to near-white. We don't need perfect binarisation.

### 4. Alignment guide overlay in TicketScanner.vue

**Choice**: Add a semi-transparent SVG rectangle overlay that covers roughly the aspect ratio of the ticket (approximately 1:2.3 portrait) centred in the viewfinder, with corner markers. No JS logic — purely CSS/SVG.

**Rationale**: Most scan failures are due to the ticket being held at an angle or partially out of frame. A visual guide costs nothing and directly addresses this.

### 5. Resolution cap: 1280 → 1920 px

**Choice**: Change `MAX` in `captureFrame` from 1280 to 1920.

**Rationale**: At 1280 px a 5×5 grid cell may be only ~40 px wide after perspective distortion. At 1920 px each cell gets ~60 px, which gives Claude meaningfully more detail. File size stays under 4 MB (a 1920×1920 JPEG at quality 0.85 is ~600 KB typically).

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Reference image cached at startup but file path wrong on Render | Use `importlib.resources` or a config-driven path with a clear error log if missing; fall back to single-image call |
| Larger uploaded images increase latency | 1920 px is still well within the 4 MB guard; Claude Vision latency is dominated by model inference, not image size |
| Canvas `filter` API not supported in old browsers | It is Baseline 2023 (Chrome 76+, Firefox 103+, Safari 15.4+); acceptable given the target audience |
| Two images in one Claude call increase token cost | The reference ticket is ~50 KB; tokens for a small PNG are minimal (<1000 image tokens) |

## Migration Plan

- No API changes; all changes are internal to service and client.
- Deploy service changes first (prompt + reference image). Client changes are independent and can deploy via Netlify on the next static build.
- If the reference image file is missing on the server, the service logs a warning and falls back to the single-image call (current behaviour).

## Open Questions

- Should the reference image be embedded directly in the Python module as a base64 literal (eliminating the file-path dependency) or remain a file read? The file read is cleaner for maintenance; the literal is more portable.
