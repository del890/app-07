## 1. Design Tokens — CSS Palette & Typography

- [x] 1.1 Update `client/app/assets/css/main.css`: replace `--background` with white (`0 0% 100%`), `--foreground` with near-black (`0 0% 10%`), `--muted` with `0 0% 96%`, `--border` with `0 0% 88%`, `--card` with `0 0% 100%`
- [x] 1.2 Add `--rule` and `--rule-2` custom properties matching the reference (`#1a1a1a22` / `#1a1a1a44`) for subtle panel dividers
- [x] 1.3 Add `--mono` custom property: `"Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace`
- [x] 1.4 Add Roboto Mono Google Fonts link (`weights=400;500`, `display=swap`) to `nuxt.config.ts` via `app.head.link`
- [x] 1.5 Verify Tailwind build succeeds with zero errors after token changes

## 2. App Shell — Header Redesign

- [x] 2.1 In `layouts/default.vue`, replace the dark-navy gradient header `style` with `background: var(--paper, #fff)` and `border-bottom: 1px solid var(--rule, rgba(0,0,0,0.13))`
- [x] 2.2 Apply `font-family: var(--mono)` and monospace text treatment to the site title link
- [x] 2.3 Remove `style="background: linear-gradient(...)"` from the `<header>` element; replace with Tailwind token classes `bg-background border-b border-border`
- [x] 2.4 Restyle nav mode-switcher pills using the updated token palette (transparent ghost style with ink borders matching reference button.ghost)

## 3. App Shell — Footer & Disclaimer

- [x] 3.1 Replace the dark-gradient footer `style` attribute with `bg-background border-t border-border text-muted-foreground`
- [x] 3.2 Remove the full-width sticky disclaimer banner from `layouts/default.vue` (the `bg-warning/10 border-b` div)
- [x] 3.3 Add a compact inline disclaimer notice to `pages/play/index.vue` (and any Play sub-pages that lack it) using a simple `<p class="text-xs text-muted-foreground mt-2">` block

## 4. Mobile Navigation — Bottom Tab Bar

- [x] 4.1 Add a `<nav>` bottom tab bar component inside `layouts/default.vue`, visible only at `sm:hidden` breakpoint (≤ 640 px), with fixed positioning and `safe-area-inset-bottom`
- [x] 4.2 Tab bar contains two NuxtLink tabs: "Pesquisa" (→ `/research`) and "Jogar" (→ `/play`), each ≥ 44 px tall
- [x] 4.3 Apply active-tab style using `useRoute` computed class binding (match current route prefix)
- [x] 4.4 Hide top-nav mode-switcher links on mobile by wrapping them with `hidden sm:flex`
- [x] 4.5 Add `pb-14` (56 px) bottom padding to `<main>` conditionally when bottom nav is visible, using `sm:pb-6` to reset on wider screens

## 5. Component Updates — Cards & Panels

- [x] 5.1 In `PredictionCard.vue`: remove any `shadow`, `border` or `card` wrapper classes that produce a visible box; replace with `border-b border-border` divider between sections
- [x] 5.2 In `ConfidenceBadge.vue`: replace any hardcoded color hex or arbitrary Tailwind values with token-mapped classes (`bg-success`, `bg-warning`, `bg-destructive` etc.)
- [x] 5.3 In `DrawSelector.vue`: ensure option buttons have `min-h-[44px]` on mobile
- [x] 5.4 In `ToolProgressTimeline.vue`: check for hardcoded navy/blue classes and replace with token-based equivalents

## 6. Page Audit — Number Badges & Touch Targets

- [x] 6.1 In `pages/index.vue`: update lottery number badge classes to `w-10 h-10` (40 px) as minimum; add `sm:w-9 sm:h-9` override only for wider screens if desired
- [x] 6.2 In `pages/play/next-draw.vue`: audit all Button components for ≥ 44 px height; add `min-h-[44px]` where needed
- [x] 6.3 In `pages/play/scan.vue`: audit scan trigger and ticket scanner interactive areas for ≥ 44 px touch targets
- [x] 6.4 Grep all `pages/**/*.vue` for hardcoded color strings (`#1A2238`, `#1e2d4a`, `blue-400`, `navy`) and replace with token-based Tailwind classes

## 7. Horizontal Padding & Spacing Audit

- [x] 7.1 In `layouts/default.vue` `<main>`: reduce default horizontal padding to `px-3 sm:px-4` for tighter mobile fit
- [x] 7.2 In `pages/index.vue` and `pages/research/index.vue`: change outer container from `max-w-3xl` to `max-w-2xl sm:max-w-3xl` to prevent excessive side padding shrinkage at 360 px
- [x] 7.3 Review `space-y-*` values on page roots; reduce top-level `py-10` to `py-6` for mobile, using `sm:py-10` to restore on wider viewports

## 8. Visual Smoke Test

- [x] 8.1 Open the app at 360 px viewport width; verify no horizontal scroll and all text is readable
- [x] 8.2 Open the app at 414 px (iPhone SE/Pro Max); verify bottom tab bar is visible and all content is accessible above it
- [x] 8.3 Open the app at 768 px (tablet); verify bottom nav is hidden and top nav is displayed
- [x] 8.4 Open the app at 1280 px (desktop); verify layout matches intended design with full nav and no bottom bar
- [x] 8.5 Navigate to `/research/*` routes; verify disclaimer banner is absent
- [x] 8.6 Navigate to `/play/*` routes; verify compact disclaimer is present and tab bar shows "Jogar" as active
