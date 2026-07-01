/**
 * Sorte UI — design tokens as plain JS.
 *
 * The CSS custom properties in `styles/tokens.css` are the source of truth at
 * runtime; this mirror is handy for charts, canvas, emails, or anywhere you
 * need token values outside of CSS.
 */

/** The ten Caixa lotteries that seed the brand palette. */
export const lotteries = [
  { id: 'lotofacil', name: 'Lotofácil', color: '#930089', accent: 'magenta', desc: 'The playful default — vivid violet UI primary.' },
  { id: 'megasena', name: 'Mega-Sena', color: '#00a868', accent: 'green', desc: 'The famous green. Also the system “go/CTA” colour.' },
  { id: 'quina', name: 'Quina', color: '#3b1c8c', accent: 'indigo', desc: 'Deep, trustworthy indigo.' },
  { id: 'lotomania', name: 'Lotomania', color: '#f78100', accent: 'orange', desc: 'Energetic orange — the system accent.' },
  { id: 'duplasena', name: 'Dupla Sena', color: '#c2173a', accent: 'red', desc: 'Bold double-chance red.' },
  { id: 'timemania', name: 'Timemania', color: '#6cbe45', accent: 'lime', desc: 'Sporty lime green.' },
  { id: 'diadesorte', name: 'Dia de Sorte', color: '#cb8e1a', accent: 'gold', desc: 'Warm lucky gold.' },
  { id: 'supersete', name: 'Super Sete', color: '#119e6c', accent: 'emerald', desc: 'Fresh emerald.' },
  { id: 'milionaria', name: '+Milionária', color: '#2b2a6e', accent: 'navy', desc: 'Premium midnight navy.' },
  { id: 'federal', name: 'Loteria Federal', color: '#134e9c', accent: 'blue', desc: 'Classic institutional blue.' },
];

export const color = {
  violet: { 50: '#f6f1ff', 100: '#ece0ff', 200: '#d8c2ff', 300: '#bd96ff', 400: '#a166fb', 500: '#8b3df5', 600: '#7826e0', 700: '#631dbb', 800: '#511a96', 900: '#3f1773' },
  green: { 50: '#e7f8f0', 100: '#c5edda', 300: '#5fcf9c', 500: '#12a85f', 600: '#0d8e4f', 700: '#0b7341' },
  orange: { 50: '#fff3e6', 100: '#ffe0bf', 400: '#ff9d33', 500: '#f78100', 600: '#d96e00' },
  red: { 50: '#fdecef', 100: '#fbd0d8', 500: '#e0234e', 600: '#c2173a' },
  neutral: { 0: '#ffffff', 50: '#f7f7f9', 100: '#efeff3', 150: '#e6e6ec', 200: '#d9d9e1', 300: '#c2c2cd', 400: '#9a9aaa', 500: '#74748a', 600: '#54546a', 700: '#3b3b4d', 800: '#262633', 900: '#15131c' },
};

export const font = {
  display: "'Poppins', ui-sans-serif, system-ui, sans-serif",
  body: "'Inter', ui-sans-serif, system-ui, sans-serif",
  size: { '2xs': '0.6875rem', xs: '0.75rem', sm: '0.875rem', md: '1rem', lg: '1.125rem', xl: '1.375rem', '2xl': '1.75rem', '3xl': '2.25rem', '4xl': '3rem' },
  weight: { regular: 400, medium: 500, semibold: 600, bold: 700, extrabold: 800 },
};

export const space = { 0: '0', 1: '0.25rem', 2: '0.5rem', 3: '0.75rem', 4: '1rem', 5: '1.5rem', 6: '2rem', 7: '2.5rem', 8: '3rem', 9: '4rem' };

export const radius = { xs: '6px', sm: '10px', md: '14px', lg: '20px', xl: '28px', pill: '999px', circle: '50%' };

export const shadow = {
  xs: '0 1px 2px rgba(21,19,28,0.06)',
  sm: '0 2px 6px rgba(21,19,28,0.08)',
  md: '0 8px 20px rgba(21,19,28,0.10)',
  lg: '0 18px 40px rgba(21,19,28,0.14)',
};

/** Valid values for the `data-theme` attribute. */
export const themes = lotteries.map((l) => l.id);

export default { lotteries, themes, color, font, space, radius, shadow };
