## Context

The `TicketScanner` component uses a 16:9 (`aspect-video`) container for the live viewfinder and the captured-image preview. Inside that container, an overlay guide rectangle is drawn portrait (`aspect-ratio: 1 / 2.3`, `width: 52%`). Because the outer box is landscape while the guide is portrait, the guide takes up only a fraction of the visible area and is flanked by large black bars — creating visual friction and making accurate framing difficult.

A Lotofácil ticket is physically portrait (roughly 1:2 proportions). Mobile users hold their phone in portrait orientation when scanning. Matching the container shape to the ticket shape is the minimal, highest-leverage fix.

## Goals / Non-Goals

**Goals:**
- Switch the camera container and preview container to portrait aspect ratio (`9/16`).
- Increase the guide rectangle's width so it fills the portrait container more completely.
- Pass `aspectRatio: 9/16` as a `getUserMedia` hint so camera hardware (if responsive) delivers a portrait-oriented stream natively.

**Non-Goals:**
- Forcing device rotation / locking screen orientation via the Screen Orientation API — too invasive and not needed.
- Redesigning the guide overlay visuals beyond proportional adjustments.
- Changing capture resolution, compression settings, or the API contract.

## Decisions

### 1. Use Tailwind's `aspect-[9/16]` arbitrary value for the container

**Choice**: Replace `aspect-video` with `aspect-[9/16]` on the `<div>` wrapping the `<video>` element and on the preview `<img>` container.

**Alternatives considered**:
- *Inline `style="aspect-ratio: 9/16"`*: Works but breaks the Tailwind-first pattern used everywhere else in the component.
- *Fixed height (e.g. `h-96`)*: Not responsive; looks bad on narrow or wide screens.

**Rationale**: `aspect-[9/16]` is the standard Tailwind idiom, generates no extra CSS, and keeps all sizing in utility classes for easy future tweaks.

### 2. Widen the guide rectangle from 52% to 75% of the container width

**Choice**: Update the inline style `width: 52%` → `width: 75%` on the guide overlay rectangle. The `aspect-ratio: 1 / 2.3` on the guide itself stays unchanged (ticket shape is correct).

**Alternatives considered**:
- *80%+*: Leaves very little margin — the ticket edge would sit almost at the container edge, making precise alignment harder on budget phone cameras with lens distortion at the edges.
- *Keep 52%*: With a portrait container the guide would still be narrow but less wasted space; however a wider guide gives more usable framing signal.

**Rationale**: 75% fills the portrait container well while leaving a visible safe-zone margin around the ticket.

### 3. Add `aspectRatio: 9/16` to the `getUserMedia` video constraints

**Choice**: Update `useTicketScanner.ts` to request `video: { facingMode: 'environment', aspectRatio: 9/16 }`.

**Alternatives considered**:
- *`width`/`height` explicit constraints*: More precise but fragile across devices; aspect-ratio hint is the correct semantic for this use case.
- *Skip the hint, rely on CSS*: The CSS container shapes the display box regardless; the stream itself may still deliver landscape frames, which `object-cover` crops. This is acceptable but the hint avoids any crop when the device honours it.

**Rationale**: The hint is non-breaking (browsers treat it as `ideal`, not `exact`) and improves behaviour on devices that support it at zero cost.

## Risks / Trade-offs

- **Desktop webcams are landscape**: On desktop the camera will ignore the `aspectRatio` hint and deliver a landscape stream. The portrait container will crop the top/bottom of the feed via `object-cover`. This is fine for scanning purposes — the ticket still fits within the guide. → No mitigation needed; same behaviour as any portrait camera UI on desktop.
- **Taller container increases page scroll**: The portrait container occupies more vertical space than the previous 16:9 box. On short-screen devices users may need to scroll slightly to reach the Capture button. → Acceptable trade-off; the guide improvement outweighs minor scroll.
