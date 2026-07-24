---
name: Premium Glassmorphism
colors:
  surface: '#111417'
  surface-dim: '#111417'
  surface-bright: '#37393d'
  surface-container-lowest: '#0b0e11'
  surface-container-low: '#191c1f'
  surface-container: '#1d2023'
  surface-container-high: '#272a2e'
  surface-container-highest: '#323538'
  on-surface: '#e1e2e7'
  on-surface-variant: '#bacac1'
  inverse-surface: '#e1e2e7'
  inverse-on-surface: '#2e3134'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#c3c6ce'
  on-secondary: '#2d3137'
  secondary-container: '#43474e'
  on-secondary-container: '#b2b5bd'
  tertiary: '#cbd4dd'
  on-tertiary: '#293138'
  tertiary-container: '#afb8c1'
  on-tertiary-container: '#404950'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe2eb'
  secondary-fixed-dim: '#c3c6ce'
  on-secondary-fixed: '#181c22'
  on-secondary-fixed-variant: '#43474e'
  tertiary-fixed: '#dbe4ed'
  tertiary-fixed-dim: '#bfc8d0'
  on-tertiary-fixed: '#141d23'
  on-tertiary-fixed-variant: '#3f484f'
  background: '#111417'
  on-background: '#e1e2e7'
  surface-variant: '#323538'
typography:
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '500'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding-desktop: 40px
  container-padding-mobile: 20px
  gutter: 24px
  component-gap: 16px
---

## Brand & Style

The design system is engineered to evoke a sense of high-tech precision and exclusive financial intelligence. Targeting a sophisticated demographic of modern investors, the UI communicates authority through a refined Dark Glassmorphism aesthetic. By blending deep, immersive backgrounds with translucent structural layers, the interface feels multi-dimensional and premium.

The emotional response is one of "calm confidence." This is achieved through a strict adherence to a "Less is More" philosophy—using heavy whitespace (or "dark space"), crisp 1px borders, and a singular, vibrant accent color to guide the eye toward critical financial insights and AI-driven actions.

## Colors

The palette is anchored by a deep charcoal base to minimize eye strain and maximize the perceived value of the content.

- **Primary (Groww Green):** Reserved exclusively for calls-to-action, success states, and indicating growth/positive trends. It must maintain a high contrast ratio against the dark background.
- **Surface Tiers:** The "Glass" effect is created using a base of `#1F2329` with varying opacity (40-60%) and a `backdrop-filter: blur(12px)`.
- **Text:** Primary text uses High-Emphasis White (90% opacity), while secondary metadata uses Medium-Emphasis Gray (60% opacity) to maintain a clear information hierarchy.

## Typography

The design system utilizes **Geist** for its technical precision and exceptional legibility in data-heavy environments. The typeface’s monospaced-influenced terminals provide a developer-grade, "high-tech" feel suitable for an AI fintech product.

- **Headlines:** Use tighter letter-spacing and heavier weights to anchor pages.
- **Body:** Generous line-height (1.6) is used to ensure financial reports and AI chat responses remain readable during long sessions.
- **Labels:** Small caps are used for secondary navigation and table headers to provide a distinct visual rhythm compared to body copy.

## Layout & Spacing

The layout follows a 12-column fluid grid for desktop and a 4-column grid for mobile. Spacing is strictly based on a 4px baseline shift to ensure mathematical harmony.

- **Chat Interface:** Centered layout with a maximum width of 800px to ensure line lengths remain optimal for reading.
- **Margins:** Large outer margins emphasize the "premium" feel by not crowding the content.
- **Breakpoints:** 
  - Mobile: < 600px (Full-width cards)
  - Tablet: 600px - 1024px (2-column data grids)
  - Desktop: > 1024px (Multi-pane view with sidebar and main chat area)

## Elevation & Depth

Depth is signaled through transparency and blurring rather than traditional heavy shadows.

- **Level 0 (Base):** Solid `#0B0E11`.
- **Level 1 (Cards/Sidebar):** Semi-transparent background with `backdrop-filter: blur(16px)` and a 1px solid border of `#1F2329`.
- **Level 2 (Modals/Popovers):** Higher opacity background with a subtle ambient glow (Shadow: `0 20px 40px rgba(0,0,0,0.4)`).
- **Interactive States:** When hovering over a glass element, the border opacity increases from 8% to 20% to provide tactile feedback.

## Shapes

The shape language balances approachability with structural discipline. 

- **Containers:** Large surfaces like chat bubbles and dashboard cards use `rounded-lg` (16px) or `rounded-xl` (24px) for a modern, soft feel.
- **Small Elements:** Buttons and input fields use `rounded-md` (8px) to maintain a crisp, professional edge.
- **Avatars:** Circular shapes are used for the AI assistant and user profiles to provide a organic contrast against the geometric grid.

## Components

- **Buttons:** 
  - *Primary:* Solid Groww Green (#00D09C) with black text. No gradient.
  - *Secondary:* Glass background with white 1px border.
- **Chat Bubbles:**
  - *AI:* Glass surface with a subtle green-tinted 1px border on the left edge.
  - *User:* Darker, solid `#1F2329` to distinguish from the AI’s transparent "ethereal" responses.
- **Inputs:** Dark backgrounds with a fixed 1px border. On focus, the border transitions to Groww Green with a soft outer glow (bloom).
- **Chips/Badges:** Small, high-radius (pill) shapes. Positive financial metrics use a subtle green background with 10% opacity and solid green text.
- **Cards:** Must feature the `backdrop-blur` effect and 1px border. No solid backgrounds allowed for top-level containers.
- **Data Visualizations:** Charts should use the Primary Green for the main data line, with a semi-transparent gradient fill (area chart) to match the glassmorphic aesthetic.