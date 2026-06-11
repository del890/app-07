## Context

The app is a Lotofácil prediction research tool built with Nuxt 3 + TypeScript + Tailwind CSS + shadcn/ui. The current visual design has:

- A **dark navy gradient header** (`#1A2238 → #1e2d4a`) that creates high contrast between the header and light page body — making the transition jarring and branding feel heavy
- shadcn/ui default card styles with explicit borders and shadows on every panel, giving a "boxed" feel that fragments the page layout
- Desktop-first spacing (`max-w-6xl`, `py-10 px-4`) that leaves insufficient breathing room on 360–414 px screens
- A **sticky bottom disclaimer banner** and a separate footer with the same dark gradient — duplicating visual weight
- No monospace type treatment for metadata, labels, or numerical readouts despite the domain being data-heavy

The reference file (`_process/index.html`) provides a proven editorial aesthetic: paper/white canvas, Roboto Mono for labels and UI chrome, transparent borderless panels, ink-on-paper token palette, and a compact sticky header with header-actions. Mobile layout is handled with simple stacked grids and generous touch targets.

## Goals / Non-Goals

**Goals:**
- Replace the dark-gradient header with a light sticky header matching the reference aesthetic
- Overhaul the CSS design-token palette (ink, paper, muted-rule) while keeping Tailwind mappings intact
- Add Roboto Mono as the UI-chrome / label typeface via Google Fonts
- Rework the default layout (`layouts/default.vue`) to remove the footer gradient and fold the disclaimer into the header bar or an unobtrusive inline notice
- Introduce a mobile bottom-tab-bar for Research / Play navigation (≤ 640 px breakpoint); keep top-nav for tablet/desktop
- Audit all page components for padding and touch-target compliance; ensure lottery number badges are ≥ 40×40 px and interactive elements ≥ 44 px
- Refresh existing component styles (PredictionCard, ConfidenceBadge, DrawSelector) to use borderless/ruled panel aesthetic

**Non-Goals:**
- Changes to API contracts, composables, or service layer
- Dark mode support (out of scope for this change)
- New pages or features beyond visual styling
- Replacing shadcn/ui primitives — style them, don't swap them

## Decisions

### D1 — Paper/Ink Token Palette (replacing navy-primary palette)

**Decision:** Replace current blue-primary dark-background tokens with an ink-on-paper palette:
- `--background: 0 0% 100%` (white paper)
- `--foreground: 0 0% 10%` (near-black ink)
- `--muted: 0 0% 96%`
- `--border: 0 0% 88%`
- Primary accent kept as a muted version of the trust-blue for interactive states

**Rationale:** The reference design proves this palette works well for data-heavy UIs. The high-contrast navy header fighting a light body was creating visual noise. A unified light canvas lets data (numbers, charts, badges) stand out rather than the chrome.

**Alternative considered:** Keep dark header, lighten body — rejected because it requires maintaining two separate color contexts and complicates future dark-mode addition.

---

### D2 — Roboto Mono for UI Chrome

**Decision:** Load Roboto Mono 400/500 via Google Fonts in `nuxt.config.ts` using `useHead` / Nuxt `app.head`. Apply it to: section labels (`.label`), badges, button text, header title, metadata readouts (seed, concurso numbers).

**Rationale:** Matches the reference aesthetic and reinforces the "research tool" identity. Monospace digits align column readouts without needing tabular-nums hacks.

**Alternative considered:** System monospace stack only — rejected because system stacks vary too widely across Android/iOS; Roboto Mono is consistent and already in the reference.

---

### D3 — Mobile Bottom Tab Bar (≤ 640 px)

**Decision:** At `sm` breakpoint and below, hide the top-nav links and show a fixed bottom bar with two tabs: "Pesquisa" and "Jogar". The bottom bar uses `safe-area-inset-bottom` padding for iOS.

**Rationale:** Primary use case on mobile is switching between research and play modes. Bottom-thumb navigation is the correct mobile pattern for two equal-weight destinations. The top nav with pill buttons becomes too small at 360 px.

**Alternative considered:** Hamburger drawer — rejected as overkill for two destinations; adds interaction cost.

---

### D4 — Remove Footer Gradient; Inline Disclaimer

**Decision:** Replace the dark-gradient footer with a single-line bordered footer (paper background, muted ink text). Move the disclaimer banner from a separate sticky band to a compact `aside` inside the Play layout only (it's only relevant in Play context).

**Rationale:** The disclaimer banner currently shows on Research pages where it's unnecessary. The dark footer repeats the header gradient and adds unnecessary visual weight on mobile (takes ~60 px of screen).

---

### D5 — Borderless Panels with Rule Dividers

**Decision:** Remove explicit `border` and `shadow` from Card components at page level. Use `border-b` rule lines and `gap` spacing to separate content sections. Keep Card borders only in dense list contexts (draw history).

**Rationale:** Reference design achieves separation purely with spacing and subtle `1px` rules at `rgba(0,0,0,0.13)` opacity. This makes pages feel lighter and more editorial.

## Risks / Trade-offs

- **[Risk] Token rename breaks Tailwind utility classes** → The Tailwind config already maps `background`, `foreground`, etc. through HSL variables. Only the raw values in `main.css` change; class names remain identical. Low risk.
- **[Risk] Roboto Mono adds ~20 KB font payload** → Load with `display=swap` and `text=` subsetting for the characters actually used in labels. Acceptable trade-off for visual consistency.
- **[Risk] Bottom tab bar overlaps content on short screens** → Add `pb-safe` / `mb-[56px]` to `<main>` when bottom nav is visible using a CSS class toggled at the `sm` breakpoint.
- **[Risk] Existing page components use hardcoded blue/navy color classes** → Audit pass required (tasks will enumerate these). Risk is incomplete audit leaving stray navy classes. Mitigation: grep for `#1A2238`, `navy`, `blue-400`, `bg-primary` and review each.

## Migration Plan

1. Update `main.css` design tokens — all pages recompute colors automatically
2. Add Roboto Mono to `nuxt.config.ts` head links
3. Refactor `layouts/default.vue` — header, disclaimer, footer, add bottom nav
4. Update global Tailwind component overrides if any in `main.css`
5. Audit and patch page/component files for mobile spacing and hardcoded colors
6. Visual smoke-test at 360 px, 414 px, 768 px, 1280 px
7. No API changes; rollback = revert CSS/layout files

## Open Questions

- Should the accent color remain trust-blue (`#2D5BFF`) or shift to a more editorial ink-red/crimson as in the reference's "ink-crimson" palette? → Default to keeping blue for continuity; can be revisited.
- Should lottery number badges use a filled or outlined style? The reference uses filled circles. → Keep filled (current), resize to ≥ 40 px on mobile.
