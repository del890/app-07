## ADDED Requirements

### Requirement: Design token foundation
The client SHALL define all colors as CSS custom properties in a single `assets/css/main.css` token block, including at minimum: `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--destructive-foreground`, `--success`, `--warning`, `--card`, `--card-foreground`, `--background`, `--foreground`, `--border`, `--input`, `--ring`, `--radius`.

#### Scenario: Token file exists and is imported
- **WHEN** the app builds
- **THEN** all CSS custom properties are defined in `:root` inside `assets/css/main.css` and imported before Tailwind utilities

#### Scenario: Tailwind maps tokens
- **WHEN** a component uses `bg-primary` or `text-primary-foreground`
- **THEN** Tailwind resolves those classes to the CSS custom property values defined in `tailwind.config.ts`

### Requirement: Single primary brand color
The client SHALL use a single primary hue (`hsl(262 52% 47%)`) as `--primary` across all modes and pages, replacing the previous per-mode color assignments (blue for research, purple for play, indigo for scenario, teal for my-draw).

#### Scenario: Navigation active state
- **WHEN** a navigation link is in the active/current-page state
- **THEN** it uses `bg-primary/10 text-primary` classes (derived from the token), not a hard-coded mode color

#### Scenario: Primary action button
- **WHEN** the user views any primary action button
- **THEN** the button background is `bg-primary` and the label is `text-primary-foreground` regardless of the current page

### Requirement: Semantic status tokens for confidence
The client SHALL express confidence levels exclusively through semantic tokens: `--success` for high confidence (≥ 70 %), `--warning` for medium confidence (40–70 %), and `--destructive` for low confidence (< 40 %).

#### Scenario: High confidence badge
- **WHEN** a prediction confidence is 70 % or above
- **THEN** the `ConfidenceBadge` component renders with `bg-success/15 text-success` classes

#### Scenario: Low confidence badge
- **WHEN** a prediction confidence is below 40 %
- **THEN** the `ConfidenceBadge` component renders with `bg-destructive/15 text-destructive` classes

### Requirement: Shadcn Vue component library installed
The client SHALL have `shadcn-vue`, `radix-vue`, `tailwind-merge`, `clsx`, and `tailwindcss-animate` installed, with Shadcn components generated under `components/ui/`.

#### Scenario: ui/ directory exists after setup
- **WHEN** the developer runs the Shadcn init command
- **THEN** `client/app/components/ui/` contains at minimum: `Button`, `Badge`, `Card` (Card/CardHeader/CardContent/CardFooter), `Input`, `Select`, and `Separator` components

#### Scenario: cn() utility available
- **WHEN** any component file imports `cn` from `~/lib/utils`
- **THEN** the function merges Tailwind class strings without duplication or conflict

### Requirement: Consistent card container style
The client SHALL use the Shadcn `Card` primitive for all card-style containers, providing uniform `rounded-lg border bg-card text-card-foreground shadow-sm` appearance and standardised padding (`p-6` for content areas).

#### Scenario: PredictionCard uses Card primitive
- **WHEN** the `PredictionCard` component is rendered
- **THEN** its outer container is a Shadcn `Card` with `CardHeader` and `CardContent` sub-components

#### Scenario: Research page cards use Card primitive
- **WHEN** any research sub-page displays a data panel
- **THEN** the panel container is a Shadcn `Card`, not a hand-crafted `div` with inline border/padding classes

### Requirement: Consistent button variants
The client SHALL replace all hand-rolled `<button>` and `<NuxtLink>` styled as buttons with the Shadcn `Button` component, using variants: `default` (primary), `secondary`, `ghost`, `outline`, and `destructive`.

#### Scenario: Generate prediction button
- **WHEN** the user views the play page generate action
- **THEN** the button is a Shadcn `Button` with `variant="default"` and `size="lg"`

#### Scenario: Back navigation link styled as ghost
- **WHEN** a back-navigation link is rendered
- **THEN** it uses `Button` with `variant="ghost"` and `asChild` wrapping a `NuxtLink`

### Requirement: Consistent badge style
The client SHALL use the Shadcn `Badge` component for all pill/badge labels, replacing manual `rounded-full` badge spans.

#### Scenario: Mode badge in navigation
- **WHEN** the active navigation mode is displayed
- **THEN** a Shadcn `Badge` component renders the label, using `variant="secondary"` with a primary-tinted class override

#### Scenario: Confidence badge
- **WHEN** `ConfidenceBadge` renders a percentage
- **THEN** it uses Shadcn `Badge` as its base, with semantic color override classes applied via `cn()`

### Requirement: Standardised spacing scale
The client SHALL apply consistent spacing rules: card content padding `p-6`, section vertical gap `gap-6`, inline element gap `gap-2`, and page horizontal padding `px-4` with vertical padding `py-6`.

#### Scenario: No mixed card padding
- **WHEN** any card component is inspected
- **THEN** padding is uniform at `p-6` (or CardContent default) — no `p-5` or `p-4` variations

#### Scenario: Section gaps are uniform
- **WHEN** a page with multiple stacked sections is rendered
- **THEN** all vertical section gaps use `gap-6` or `space-y-6`, not a mix of `mb-4`, `mb-6`, `mb-8`

### Requirement: Navigation shell uses Shadcn primitives
The client's default layout (header and footer) SHALL use Shadcn `Separator` for dividers and structured navigation markup aligned with Shadcn NavigationMenu conventions.

#### Scenario: Header bottom border uses Separator
- **WHEN** the default layout renders
- **THEN** the header/content boundary is a Shadcn `Separator` component, not a `border-b` CSS class on a container div

#### Scenario: Footer top border uses Separator
- **WHEN** the default layout renders
- **THEN** the footer/content boundary is a Shadcn `Separator` component
