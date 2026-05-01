## 1. Install & Bootstrap Shadcn Vue

- [x] 1.1 Install dependencies: `npm install radix-vue tailwind-merge clsx tailwindcss-animate` in `client/`
- [x] 1.2 Install `shadcn-vue` CLI and run `npx shadcn-vue@latest init` — accept defaults, set base color to custom, output to `components/ui/`
- [x] 1.3 Verify `client/app/components/ui/` directory was created with at least one component file
- [x] 1.4 Verify `client/lib/utils.ts` contains the `cn()` helper (`clsx` + `tailwind-merge`)

## 2. Configure Design Tokens

- [x] 2.1 Edit `client/assets/css/main.css` (or create it) to define `:root` CSS custom properties for all tokens: `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--destructive-foreground`, `--success`, `--warning`, `--card`, `--card-foreground`, `--background`, `--foreground`, `--border`, `--input`, `--ring`, `--radius`
- [x] 2.2 Set `--primary` to `262 52% 47%` (HSL without `hsl()` wrapper, as Shadcn convention requires)
- [x] 2.3 Set `--success` to `142 71% 45%`, `--warning` to `38 92% 50%`, `--destructive` to `0 84% 60%`
- [x] 2.4 Update `client/tailwind.config.ts` to extend colors with `primary`, `primary-foreground`, `success`, `warning`, `destructive`, and all other tokens mapped to `hsl(var(--<token>))` pattern
- [x] 2.5 Ensure `tailwindcss-animate` plugin is added to `plugins` array in `tailwind.config.ts`
- [x] 2.6 Ensure `main.css` is imported in `nuxt.config.ts` CSS array (before other styles)

## 3. Add Shadcn UI Components

- [x] 3.1 Add Shadcn `Button` component: `npx shadcn-vue@latest add button`
- [x] 3.2 Add Shadcn `Badge` component: `npx shadcn-vue@latest add badge`
- [x] 3.3 Add Shadcn `Card` component (generates Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription): `npx shadcn-vue@latest add card`
- [x] 3.4 Add Shadcn `Input` component: `npx shadcn-vue@latest add input`
- [x] 3.5 Add Shadcn `Select` component: `npx shadcn-vue@latest add select`
- [x] 3.6 Add Shadcn `Separator` component: `npx shadcn-vue@latest add separator`

## 4. Update Layout Shell

- [ ] 4.1 Edit `client/app/layouts/default.vue` — replace header bottom `border-b` div with `<Separator>` component
- [ ] 4.2 Edit `client/app/layouts/default.vue` — replace footer top `border-t` div with `<Separator>` component
- [ ] 4.3 Replace mode-specific nav badge colors (blue/purple classes) in the header with a single `Badge` component using `variant="secondary"` + `text-primary` override
- [ ] 4.4 Verify layout renders correctly with no visual regressions

## 5. Refactor Shared Components

- [ ] 5.1 Edit `client/app/components/ConfidenceBadge.vue` — replace hand-rolled badge markup with Shadcn `Badge`; map green/yellow/red classes to `bg-success/15 text-success`, `bg-warning/15 text-warning`, `bg-destructive/15 text-destructive` using `cn()`
- [ ] 5.2 Edit `client/app/components/PredictionCard.vue` — wrap outer container with Shadcn `Card`/`CardHeader`/`CardContent`; replace any inline padding `p-5`/`p-6` with CardContent default
- [ ] 5.3 Edit `client/app/components/DrawSelector.vue` — replace selected number button classes with `bg-primary text-primary-foreground`; unselected stays `bg-muted text-muted-foreground`
- [ ] 5.4 Edit `client/app/components/ToolProgressTimeline.vue` — update running/completed step colors to use `text-primary` (running) and `text-success` (completed) tokens
- [ ] 5.5 Edit `client/app/components/TicketScanner.vue` — replace any custom button or card classes with Shadcn `Button`/`Card` equivalents

## 6. Refactor Page-Level Buttons & Links

- [ ] 6.1 Edit `client/app/pages/index.vue` — replace styled `<button>` and `<NuxtLink>` as buttons with Shadcn `Button` (`variant="default"` for primary, `variant="secondary"` for secondary actions)
- [ ] 6.2 Audit `client/app/pages/play/` directory — replace all `<button>` and link-as-button patterns with Shadcn `Button`
- [ ] 6.3 Audit `client/app/pages/research/` directory — replace all `<button>` and link-as-button patterns with Shadcn `Button`
- [ ] 6.4 Replace all back-navigation links (`text-sm text-blue-600 hover:underline`) with `Button variant="ghost" asChild` wrapping `NuxtLink`

## 7. Refactor Page-Level Cards & Containers

- [ ] 7.1 Audit research sub-pages — replace all `<div class="... border border-gray-200 ... rounded-lg">` card containers with Shadcn `Card`
- [ ] 7.2 Standardise all card content padding to `p-6` (via `CardContent`) — remove any `p-5` or `p-4` card padding found
- [ ] 7.3 Standardise section vertical gaps to `gap-6` or `space-y-6` — remove mixed `mb-4`/`mb-6`/`mb-8` patterns between sections

## 8. Refactor Form Inputs

- [ ] 8.1 Audit `client/app/pages/research/` — replace styled `<input type="text">` and `<input type="number">` elements with Shadcn `Input`
- [ ] 8.2 Audit `client/app/pages/research/` — replace styled `<select>` elements with Shadcn `Select`/`SelectTrigger`/`SelectContent`/`SelectItem`
- [ ] 8.3 Verify form inputs retain their existing `v-model` bindings and emit behaviour after replacement

## 9. Remove Retired Mode-Specific Color Classes

- [ ] 9.1 Search all `.vue` files for hard-coded mode colors (`blue-600`, `blue-100`, `blue-800`, `indigo-600`, `indigo-50`, `teal-600`, `teal-50`) and replace with token-based equivalents (`primary`, `muted`, `accent`)
- [ ] 9.2 Remove `bg-purple-600`, `hover:bg-purple-700`, etc. from templates where Shadcn `Button` now handles styling
- [ ] 9.3 Remove amber disclaimer banner hard-coded colors; map to `bg-warning/10 border-warning/30 text-warning-foreground` tokens if applicable

## 10. QA & Cleanup

- [ ] 10.1 Run `npm run lint` in `client/` — fix all ESLint errors
- [ ] 10.2 Run `npm run test` in `client/` — verify all existing composable/unit tests still pass
- [ ] 10.3 Manual smoke test: open index page, navigate to play/next-draw, trigger a prediction, verify styling looks correct and consistent
- [ ] 10.4 Manual smoke test: navigate to research mode, check frequency table, draw history — verify cards, inputs, and badges render correctly
- [ ] 10.5 Check mobile viewport (375 px) in browser dev tools — verify no overflow or broken layout
- [ ] 10.6 Delete any remaining one-off badge `<span>` patterns or hard-coded border/padding combos that escaped the audit
