## Context

The client is a Nuxt 3 / TypeScript app styled exclusively with Tailwind CSS utility classes. Over several incremental feature deliveries, colors, spacing, and component patterns drifted: blue, purple, indigo, and teal are all used as "primary" depending on the mode, card padding varies from `p-5` to `p-6`, badge pills are hand-rolled three different ways, and there is no central token file that could be updated to re-skin the whole app.

Shadcn Vue is the natural fit here: it ships unstyled-by-default Radix Vue primitives wrapped in components that accept a CSS custom-property theme. We get accessible, composable building blocks (Button, Badge, Card, Input, Select, NavigationMenu) plus the token layer (`--primary`, `--muted`, `--destructive`, etc.) that unifies every component. The install is additive — we bring in only what we use — and the output is still plain Tailwind classes the team already knows.

## Goals / Non-Goals

**Goals:**
- Single source of truth for colors via CSS custom properties in `assets/css/main.css` + Tailwind token mapping in `tailwind.config.ts`
- Consistent spacing scale for cards (`p-6`), section gaps (`gap-4`/`gap-6`), and page padding (`px-4 py-6`)
- Replace all hand-rolled buttons, badges, card containers, and basic form inputs with Shadcn Vue counterparts
- Navigation shell (header, footer) rebuilt with Shadcn NavigationMenu and Separator
- Single brand hue (`hsl(262 52% 47%)` — the app's purple) as the primary token; semantic aliases for success/warning/destructive derived from it; mode-specific accent removed (play and research share the same primary)
- All changes confined to the client; zero service-layer or API-contract modifications

**Non-Goals:**
- Redesigning information architecture or page flows
- Changing data-fetching logic or composables
- Adding dark mode (token layer is prepared for it but not activated in this change)
- Performance optimisation beyond what Shadcn's tree-shaking provides
- Copy/translation changes

## Decisions

### D1 — Shadcn Vue over alternatives (Nuxt UI, PrimeVue, Headless UI)

**Chosen:** Shadcn Vue (`shadcn-vue.com`)

**Rationale:**
- Components are copied into `components/ui/` as editable source, not an opaque dependency — full control over styling without fork risk
- Radix Vue primitives provide WAI-ARIA compliance out of the box
- Uses the same Tailwind class conventions already in the codebase
- CSS variable token system is the narrowest seam to wire up: one `main.css` block and one `tailwind.config.ts` change

**Alternatives considered:**
- **Nuxt UI**: Opinionated, heavier; conflicts with existing component naming; colours driven by module config rather than CSS vars
- **PrimeVue**: Separate theming system; large bundle; overkill for the current scale
- **Headless UI (for Vue)**: Lower-level than Radix; no ready-made Button/Card/Badge, meaning we'd build the same things manually anyway

### D2 — Single brand hue, semantic token aliasing

Replace the current four-colour mode system (blue/purple/indigo/teal) with one primary hue and semantic aliases:

| Token | Value | Usage |
|---|---|---|
| `--primary` | `262 52% 47%` (purple) | Buttons, active nav, selected states |
| `--muted` | `240 4.8% 95.9%` | Secondary surfaces, inactive states |
| `--success` | `142 71% 45%` | Confidence ≥ 70%, valid states |
| `--warning` | `38 92% 50%` | Confidence 40–70%, caution banners |
| `--destructive` | `0 84% 60%` | Confidence < 40%, errors |
| `--accent` | `262 30% 92%` | Subtle highlight backgrounds |

Mode-specific colors (blue for research, teal for my-draw) are retired; the single primary token is used everywhere, reducing cognitive load.

### D3 — Incremental component swap, no big-bang rewrite

Replace components file-by-file rather than rewriting every template at once. Sequence:
1. Install Shadcn Vue, configure tokens (`tailwind.config.ts`, `assets/css/main.css`)
2. Layout shell (default.vue) — highest impact, fewest touch points
3. Shared components (Button, Badge, Card) — used everywhere; single replacement normalises the whole app
4. Page-level forms and inputs (research pages, play pages)

Each step is independently reviewable and testable.

### D4 — Keep `cn()` utility, adopt it project-wide

Shadcn's `lib/utils.ts` ships a `cn()` helper (wraps `clsx` + `tailwind-merge`). All new and updated components will use it. This is the only non-UI runtime addition.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Shadcn component copy diverges from upstream over time | Pin the Radix Vue peer dep; only re-pull Shadcn components if a bug fix is needed; document in repo memory |
| Mode-colour removal surprises users who associate purple = play, blue = research | Subtle section headers or page-level descriptors already communicate mode context in Portuguese; validate in a quick manual review pass |
| CSS custom property names clash with existing Tailwind classes | Shadcn uses `hsl()` wrapper convention; no collision with standard Tailwind palette names. Check `globals.css` import order — must come before Tailwind utilities |
| `tailwind-merge` version conflict with existing `clsx` usage | Add `tailwind-merge` fresh; there is no existing `clsx` dep — no conflict |
| Bundle size increase | Radix Vue primitives are tree-shaken; only imported components are bundled. Acceptable trade-off for accessibility and consistency gains |

## Migration Plan

1. `npm install shadcn-vue radix-vue tailwind-merge clsx tailwindcss-animate` in `client/`
2. Run `npx shadcn-vue@latest init` to generate `components/ui/`, `lib/utils.ts`, and update `tailwind.config.ts` + `assets/css/main.css`
3. Commit the baseline scaffold as a standalone commit before touching existing components
4. Replace components in sequence per D3 — layout shell → shared components → page forms
5. Remove now-unused ad-hoc color utility classes from replaced templates
6. Run `npm run lint` and `npm run test` after each phase; fix regressions before the next phase
7. **Rollback**: Because changes are file-level and non-breaking to the API surface, reverting any individual commit restores the previous state

## Open Questions

- Should the `DrawSelector` number grid keep purple for selected numbers post-token migration, or use the new `--primary` token? (They converge to the same hue; confirm visually)
- Sticky header vs. static header — worth addressing in this change or defer?
