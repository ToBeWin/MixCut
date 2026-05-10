---
name: Cinematic Studio
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#849495'
  outline-variant: '#3b494b'
  surface-tint: '#00dbe9'
  primary: '#dbfcff'
  on-primary: '#00363a'
  primary-container: '#00f0ff'
  on-primary-container: '#006970'
  inverse-primary: '#006970'
  secondary: '#ffdb9d'
  on-secondary: '#412d00'
  secondary-container: '#feb700'
  on-secondary-container: '#6b4b00'
  tertiary: '#f5f5f5'
  on-tertiary: '#2f3131'
  tertiary-container: '#d9d9d9'
  on-tertiary-container: '#5d5f5f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#7df4ff'
  primary-fixed-dim: '#00dbe9'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#ffdea8'
  secondary-fixed-dim: '#ffba20'
  on-secondary-fixed: '#271900'
  on-secondary-fixed-variant: '#5e4200'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: '1.4'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  mono-code:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 1px
  panel-padding: 12px
  container-gap: 16px
  margin-sm: 8px
  margin-md: 16px
  margin-lg: 24px
---

## Brand & Style

This design system is engineered for high-performance creative workflows, prioritizing extreme focus and technical precision. The aesthetic draws from high-end video post-production suites and professional hardware interfaces. It utilizes a **Corporate Modern** foundation fused with **Glassmorphism** to provide depth without distracting the user from their media.

The mood is "Cinematic Dark"—a low-light environment that reduces eye strain during long editing sessions and ensures that the colors of the video content remain the focal point. Surfaces are layered to create a clear functional hierarchy, using "obsidian" depth to separate timelines, inspectors, and asset libraries.

## Colors

The palette is strictly functional, utilizing a "Lights Out" philosophy to maximize screen real estate for the video preview. 

- **Foundation:** Deep Charcoal (#121212) serves as the base application background. Graphite (#1E1E1E) is used for primary interface panels (Timeline, Bin, Inspector).
- **Accents:** Electric Cyan (#00F0FF) is reserved exclusively for interactive states, progress indicators, and AI-driven features. Soft Amber (#FFB800) provides a non-aggressive warning state for dropped frames or offline media.
- **Contrast:** Text and primary icons use Crisp White (#FFFFFF) and high-range grays to maintain legibility against the dark void of the UI.

## Typography

This design system employs a compact typographic scale to accommodate information-dense panels. **Inter** is the primary typeface, chosen for its exceptional legibility at small sizes and its neutral, professional tone. 

For technical readouts—such as timecodes, frame rates, and file metadata—**JetBrains Mono** is introduced to provide a clear distinction between UI labels and raw data values. All "label-caps" styles should be used sparingly for section headers within panels to maintain a clean, structured look.

## Layout & Spacing

The layout follows a **Fixed-Panel Grid** system. Unlike standard web layouts, this system treats the screen as a workspace of tiled "modules." 

- **Gutters:** A micro-gutter of 1px (using the border color #2A2A2A) separates main workspace modules to maximize screen space.
- **Density:** Elements are tightly packed using a 4px baseline grid. 
- **Adaptation:** On desktop, panels are resizable and dockable. On mobile, the UI reflows into a single-column stack with the video preview pinned to the top, utilizing a bottom-sheet pattern for the timeline and tools.

## Elevation & Depth

Elevation is expressed through **Tonal Layering** and **Glassy Overlays** rather than traditional drop shadows.

1.  **Level 0 (Base):** #121212 - The main application background.
2.  **Level 1 (Panels):** #1E1E1E - Timeline and Inspector surfaces.
3.  **Level 2 (Active/Floating):** #2A2A2A - Hover states and context menus.
4.  **Glass Overlays:** Modals and tooltips use a semi-transparent version of #1E1E1E (80% opacity) with a 20px background blur (backdrop-filter) to maintain context of the underlying project.

Borders are strictly 1px wide and use #2A2A2A to define edges without creating visual noise.

## Shapes

The shape language is **Soft** but leans towards geometric precision. A default radius of 4px (`rounded-sm`) is used for buttons, input fields, and panels to maintain a professional, high-fidelity look. 

- **Tool Icons:** Encased in square containers with subtle 2px rounding.
- **Timeline Clips:** Use a 4px radius to ensure they feel like distinct, draggable units of media.
- **Active State Indicators:** Use sharp, 1px vertical bars or 2px underlines in Electric Cyan.

## Components

- **Buttons:** Primary buttons use a ghost style (Cyan border and text) or solid Cyan with black text for high-priority actions. Secondary buttons are #2A2A2A with white text.
- **Timeline Clips:** Represented as blocks with a subtle inner glow when selected. AI-processed clips feature a Cyan "pulse" on the top border.
- **Input Fields:** Darker than the panel surface (#121212), with a 1px #2A2A2A border that turns Cyan on focus.
- **Icons:** Use the Lucide library with a 1.5pt stroke weight. Icons should be monochrome white at 70% opacity, shifting to 100% opacity Cyan on hover or active state.
- **Scrubbers & Sliders:** Thin, high-contrast tracks with a Cyan handle. The handle should expand slightly when interacted with.
- **Context Menus:** High-blur glass surfaces with 1px borders, using 8px vertical padding between items.