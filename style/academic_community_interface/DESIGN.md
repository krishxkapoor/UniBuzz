---
name: Academic Community Interface
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf4'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dde9ff'
  surface-container-highest: '#d5e3fd'
  on-surface: '#0d1c2f'
  on-surface-variant: '#44474e'
  inverse-surface: '#233144'
  inverse-on-surface: '#ebf1ff'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#465f88'
  primary: '#000a1e'
  on-primary: '#ffffff'
  primary-container: '#002147'
  on-primary-container: '#708ab5'
  inverse-primary: '#aec7f6'
  secondary: '#775a19'
  on-secondary: '#ffffff'
  secondary-container: '#fed488'
  on-secondary-container: '#785a1a'
  tertiary: '#190021'
  on-tertiary: '#ffffff'
  tertiary-container: '#3e004c'
  on-tertiary-container: '#bc68cb'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#aec7f6'
  on-primary-fixed: '#001b3d'
  on-primary-fixed-variant: '#2d476f'
  secondary-fixed: '#ffdea5'
  secondary-fixed-dim: '#e9c176'
  on-secondary-fixed: '#261900'
  on-secondary-fixed-variant: '#5d4201'
  tertiary-fixed: '#fed6ff'
  tertiary-fixed-dim: '#f6adff'
  on-tertiary-fixed: '#350041'
  on-tertiary-fixed-variant: '#712183'
  background: '#f8f9ff'
  on-background: '#0d1c2f'
  surface-variant: '#d5e3fd'
typography:
  h1:
    fontFamily: Newsreader
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.25'
    letterSpacing: -0.01em
  h3:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
    letterSpacing: 0em
  body-lg:
    fontFamily: Work Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  body-md:
    fontFamily: Work Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0em
  body-sm:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: 0.01em
  label-caps:
    fontFamily: Work Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  button:
    fontFamily: Work Sans
    fontSize: 15px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  container-max: 1280px
  gutter: 24px
  margin: 32px
---

## Brand & Style

The brand personality is authoritative yet accessible, bridging the gap between traditional academic excellence and modern digital connectivity. It is designed to evoke feelings of belonging, intellectual rigor, and institutional trust. 

The design style follows a **Corporate / Modern** approach with a focus on **Minimalism**. It utilizes generous whitespace to reduce cognitive load, allowing dense academic information to breathe. The aesthetic prioritizes structural clarity and high-contrast legibility, ensuring that the platform feels like a professional tool for students, faculty, and alumni rather than a disruptive entertainment app.

## Colors

The palette is anchored by a deep navy ("Oxford Blue") to establish institutional gravity. Gold is used as a high-intent secondary accent for calls-to-action and meaningful highlights, representing achievement and tradition. 

- **Primary:** Deep navy for navigation, primary buttons, and structural headers.
- **Secondary:** Gold for interactive accents, badges, and focus states.
- **Neutral:** Slate grays for body text, borders, and secondary metadata.
- **Semantic:** Standardized success and error colors are slightly desaturated to maintain the professional tone.
- **Backgrounds:** A soft off-white (Slate-50) is used for the page background to reduce eye strain, while pure white is reserved for card surfaces.

## Typography

The typography strategy employs a pairing of a traditional serif and a functional sans-serif to mirror the duality of university life (heritage vs. modern utility).

- **Headings:** Use *Newsreader* for all editorial and page-level titles. Its literary qualities emphasize the "academic" nature of the content.
- **Interface & Body:** Use *Work Sans* for all UI elements, navigation, and long-form feed content. It provides exceptional legibility at small sizes and maintains a professional, neutral tone.
- **Formatting:** Headlines should use optical kerning and tight line-heights, while body text requires generous leading (1.5x+) to ensure accessibility for research-heavy reading.

## Layout & Spacing

This design system utilizes a **Fixed Grid** for large screens and a **Fluid Grid** for mobile devices. 

- **Grid System:** A 12-column grid with 24px gutters. Content is centered in a 1280px container.
- **Vertical Rhythm:** An 8px base unit (with a 4px sub-grid) governs all vertical spacing.
- **Feed Layout:** Cards are vertically stacked with 24px gaps. Sidebars (for navigation and trending topics) follow a 1/4 or 1/3 column span respectively.
- **Data Tables:** Use high-density spacing (8px cell padding) for management views to maximize information density.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Low-contrast outlines** rather than heavy shadows. This maintains the clean, "paper-like" academic feel.

- **Level 0 (Background):** Used for the main canvas, colored in the neutral background hex.
- **Level 1 (Cards/Surface):** Pure white background with a 1px border (#E2E8F0).
- **Level 2 (Hover/Active):** A soft, diffused shadow (0px 4px 12px rgba(0, 33, 71, 0.08)) is applied when a card is interacted with.
- **Navigation:** Fixed top bars use a subtle bottom border rather than a shadow to maintain a flat, professional profile.

## Shapes

The shape language is **Soft (1)**, opting for a subtle 0.25rem (4px) radius on most components. This choice balances the rigidity of academic structures with the friendliness of a social platform.

- **Primary Buttons & Inputs:** 4px radius.
- **Cards & Containers:** 8px (Large) radius.
- **Avatars:** Circular (Full round) to humanize the community aspect.
- **Tags/Chips:** Semi-pill (12px) to distinguish them from actionable buttons.

## Components

- **Cards:** The primary container for the feed. Cards should have a 1px slate-200 border, white background, and 24px internal padding. Title text should use the serif font (h3).
- **Navigation:** A persistent sidebar or top-nav using the primary navy color. Links should have a gold left-border indicator when active.
- **Buttons:** 
  - *Primary:* Navy background, white text, 4px radius.
  - *Secondary:* Gold background, navy text (high contrast).
  - *Ghost:* No background, navy border, 1px.
- **Input Fields:** Labeled with Work Sans (label-caps). Background should be white with a 1px slate-300 border, turning primary-navy on focus.
- **Data Tables:** Designed for the admin dashboard. Use a 12px font size for row data with alternating row highlights (Slate-50). Headers must be sticky with a bold Work Sans label.
- **Campus Badges:** Small, high-contrast chips used to denote "Faculty," "Student," or "Alumni," using the secondary or tertiary colors for differentiation.