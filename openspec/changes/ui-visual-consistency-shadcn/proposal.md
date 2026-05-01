## Why

The current UI was built incrementally without a unified design system, resulting in inconsistent color usage across modes (blue, purple, indigo, teal all competing), uneven spacing, and visual noise that detracts from the clean, trust-inspiring experience this kind of analytical tool requires. Introducing Shadcn Vue gives us composable, accessible primitives and a design token foundation so all future UI work converges on the same visual language.

## What Changes

- Introduce Shadcn Vue as the component library, configured with a custom theme aligned to the app's brand
- Define a consolidated color palette (primary brand color + neutral scale + semantic status colors) as Tailwind/CSS design tokens, replacing ad-hoc color picks scattered across files
- Standardise spacing scale: consistent card padding, section gaps, and content margins across all pages
- Refactor navigation and layout shell (header, footer, page wrapper) to use Shadcn primitives (NavigationMenu, Badge, Separator)
- Replace ad-hoc button styles with Shadcn `Button` variants (primary, secondary, ghost, destructive)
- Replace manual badge/pill implementations with Shadcn `Badge`
- Unify card containers to use Shadcn `Card` (Card, CardHeader, CardContent, CardFooter)
- Standardise form inputs (text, number, select) with Shadcn `Input` and `Select`
- Replace confidence badge with a consistent Shadcn-based component using semantic status tokens
- Ensure all interactive elements have coherent focus, hover, and disabled states from the shared token set
- Keep UI text in Brazilian Portuguese; no copy changes

## Capabilities

### New Capabilities

- `design-system`: Centralised color tokens, spacing rules, and typography scale powering the entire client UI

### Modified Capabilities

- (none — existing page behaviour and data-flow are unchanged; only visual layer is updated)

## Impact

- **Client only** — no service or API changes
- Adds `shadcn-vue` and `radix-vue` packages to `client/package.json`; requires `tailwindcss-animate` plugin
- All existing component files will be updated in-place; no new pages or routes
- Tailwind config will gain CSS custom-property–based color tokens
- Build output size may increase slightly from Radix primitives, but tree-shaking keeps it minimal
