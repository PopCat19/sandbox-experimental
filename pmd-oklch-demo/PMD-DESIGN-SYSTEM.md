# Project Minimalist Design (PMD) Specification

## Overview

Project Minimalist Design (PMD) is a design system tangentially inspired by Material Design 3, built on principles of simplicity and practicality. The system emphasizes YAGNI (You Aren't Gonna Need It) and DRY (Don't Repeat Yourself) principles through its Figma-based foundation. PMD serves as a flexible design guideline rather than strict compliance framework, encouraging consistent visual hierarchy across UI/UX projects.

## Design Philosophy

PMD distinctively emphasizes visibility through lightness, opacity, weight, spacing, radius, and direction rather than decorative elements. Gradients and shadows are intentionally avoided unless hierarchical clarity demands their use, maintaining clean visual separation.

### Core Principles
- **YAGNI (You Aren't Gonna Need It)**: Avoid unnecessary complexity
- **DRY (Don't Repeat Yourself)**: Eliminate redundancy through systematic variable usage
- **Practical Applicability**: Adapt guidelines contextually rather than rigid specification
- **Inheritance-Based Architecture**: Systematic consistency through variable cascading
- **Broad Compatibility**: Support diverse project requirements without pre-built components

## Scale System

All measurements utilize rem units with base-16 (16px = 1rem) for consistent scaling across viewports.

### Standard Increments
Following 2, 4, and 8-pixel patterns expressed as rem values:

**Regular Scale:**
- 0.5rem (8px)
- 0.625rem (10px)
- 0.75rem (12px)
- 1rem (16px)
- 1.25rem (20px)
- 1.5rem (24px)
- 1.75rem (28px)
- 2rem (32px)
- 2.5rem (40px)
- 3rem (48px)
- 4rem (64px)
- 4.5rem (72px)
- 5rem (80px)
- 5.5rem (88px)
- 6rem (96px)
- 6.5rem (104px)
- 7rem (112px)
- 7.5rem (120px)
- 8rem (128px)
- 10rem (160px)
- 11.25rem (180px)
- 12.5rem (200px)
- 13.75rem (220px)
- 15rem (240px)
- 16rem (256px)
- 17.5rem (280px)

**Large Scale Values:**
- 32rem (512px)
- 48rem (768px)
- 64rem (1024px)
- 128rem (2048px)

**Edge Cases (Unlikely Usage):**
- 256rem (4096px)
- 512rem (8192px)

*Note: Actual values depend on viewport resolution and perceived object scale, with bracketed values unlikely to be used in typical implementations.*

## Border Radius

### Standard Values
- 0.25rem (4px)
- 0.5rem (8px)
- 0.75rem (12px)
- 1.5rem (24px)
- 2rem (32px)
- 2.5rem (40px)
- 3rem (48px)
- 4rem (64px)
- 5rem (80px)
- 8rem (128px)
- 9999px (fully rounded regardless of size)

### Grouped Component Pattern
For visual connection between grouped components:
- Use 0.5rem (8px) on relative sides to contrast
- Example: `1rem 0.5rem 0.5rem 1rem` combined with `0.5rem 1rem 1rem 0.5rem` for adjacent elements
- Radius selection should reflect element importance and relationship to surrounding components

## Borders

### Standard Widths
- 0 (no border)
- 0.125rem (2px)
- 0.25rem (4px)
- 0.375rem (6px)
- 0.5rem (8px)
- 0.625rem (10px)
- 0.75rem (12px)
- 1rem (16px)

### Edge Case Values
- 1.5rem (24px)
- 2.5rem (40px)

**Default:** 0.125rem (2px) for standard framing requirements

*Thicker borders denote increased priority or active states within the hierarchy.*

## Opacity

### Standard Percentages
- 0%
- 8%
- 12%
- 16%
- 24%
- 32%
- 40%
- 64%
- 80%
- 96%
- 100%

### Simplified Values
When granular control is unnecessary:
- 10%
- 20%
- 40%
- 60%
- 80%

*Lower opacity values create subtle layering and depth, while higher values demand attention.*

## Color System

The color system partitions variables based on lightness, opacity, and usage, formatted as `<lightness%>x<opacity%><+hue-offset>`. All color definitions assume dark scheme by default. Variables are designed to be mutable, allowing global theme adjustments through hue rotation and chroma modification.

### Color Hierarchy

#### White/100x
- **Usage:** Highest priority neutral tintable elements
- **Lightness:** 100%
- **Opacity Variants:** 100%, 32% (for selection/hover states)

#### 88x (Primary)
- **Usage:** Main header elements, CTA elements, icons, enabled states
- **Lightness:** 88%
- **Opacity Variants:**
  - 100% (full visibility)
  - 48% (inactive track elements)
  - 24% (disabled states and disabled outlines)

#### 88x+12 (PrimaryAux)
- **Usage:** Primary auxiliary with +180° complementary hue offset
- **Lightness:** 88%
- **Hue Offset:** +180° (complementary)
- **Example Use:** Pipewire boost indicators

#### 80x (Secondary)
- **Usage:** Body elements
- **Lightness:** 80%
- **Surface Layers:** 8% or 12% opacity
- **Position:** Above 8x Base layer
- **Example Use:** Message containers, button text

#### 80x+12 (SecondaryAux)
- **Usage:** Secondary auxiliary with +180° complementary hue offset
- **Lightness:** 80%
- **Hue Offset:** +180° (complementary)

#### 64x (Accent)
- **Usage:** Occupied and actionable elements
- **Lightness:** 64%
- **Example Use:** Hyperlinks, clear actions, interactive states

*Note: In OKLCH conversion, this maps to 72% lightness due to perceptual adjustments.*

#### 8x (Base)
- **Usage:** Solid frames, typically containing surface layers or components
- **Lightness:** 8%
- **Opacity Variants:**
  - 100% (solid foundation)
  - 80% (album artwork tinting)
  - 64% (semi-translucent)
  - 40% (with 24% backdrop blur for bar surfaces)
- **Special Applications:**
  - CTA text/icons at 40% with backdrop blur
  - Album artwork tinting at 80%
  - Modal overlays at 80% to dim backgrounds

#### Black/0x
- **Usage:** Low priority neutral tintable elements
- **Lightness:** 0%
- **Opacity Variants:** 100%, 80%, 64%, 40%

## OKLCH Conversion

Color values convert to OKLCH colorspace (sRGB clamped) with hue shifted approximately 30° compared to HSL.

### Key Hue Reference Points
- Red: 30°
- Yellow: 90°
- Green: 140°
- Cyan/Teal: 195°
- Blue: 260°
- Magenta: 330°

### Conversion Mappings
```
100x = oklch(1 0 0)
88x = oklch(0.88 0.056 0)
80x = oklch(0.8 0.1 0)
64x = oklch(0.72 0.122 0)
8x = oklch(0.2 0.032 0)
0x = oklch(0 0 0)
```

*OKLCH provides perceptually uniform color manipulation, essential for consistent lightness transitions across hue rotations.*

## Reference Palette

Example derived from PMQuickshellMockup (1440x1024 viewport) with root hue 345° and auxiliary hue 75°:

```
100x: #FFFFFF [100%, 32%]
88x: #FFC2D1 [100%, 24%]
88x+12: #C2FFF0 [100%, 24%]
80x: #FF99B2 [100%, 48%, 12%, 8%]
80x+12: #99FFE5 [100%, 48%, 12%, 8%]
64x: #FF4775 [100%, 80%]
8x: #1E0B10 [100%, 80%, 64%, 40%]
0x: #000000 [100%, 80%, 64%, 40%]
```

*These values demonstrate the system applied with pink-based primary hue and teal complementary accent.*

## Typography

Font variables partition based on hierarchical priority, utilizing rounded Google Fonts and practical Nerdfonts with automatic line-height.

### Font Hierarchy

#### Bold Typeface
- **Fonts:** Fredoka Bold, Rounded Mplus 1c Bold
- **Usage:** Major header and subtext elements
- **Scales:** 3rem (48px), 2.5rem (40px), 1rem (16px), 0.5rem (8px)
- **Note:** Weight and lightness primarily determine hierarchy over size differences

#### Semibold Typeface
- **Font:** Fredoka SemiBold
- **Usage:** Section headers and titles
- **Scales:** 1rem (16px), 0.75rem (12px), 0.625rem (10px)

#### Medium Typeface
- **Fonts:** Fredoka Medium, Rounded Mplus 1c Medium
- **Usage:** Body elements including paragraphs and hyperlinks
- **Scales:** 1.25rem (20px), 1rem (16px), 0.75rem (12px), 0.625rem (10px)

#### Mono Typeface
- **Font:** FiraCode Nerd Font
- **Usage:** Monospace elements like code snippets and Nerd Font icons
- **Scales:** 1.25rem (20px), 1rem (16px), 0.75rem (12px), 0.625rem (10px)

### Icon Sizing
- **Text Adjacent:** Typically exceed accompanying text by 0.25-0.5rem (4-8px)
- **Standalone:** 1.5rem (24px) or 1rem (16px) as standard dimensions
- **Header Elements:** May differ by ±0.25-1rem (±4-16px) from Medium scale

*Note: Lightness and weight primarily communicate hierarchy over size differences.*

## Frame Conventions

Standard frame specifications for dark scheme implementation:

### Basic Specifications
- **Border:** 0.125rem (2px) default width
- **Corner Radius:** 1rem (16px) or 0.5rem (8px) depending on element prominence
- **Spacing:** 0.5rem (8px) or 0.25rem (4px) internal padding

### State-Specific Colors
- **Boost:** 88x+12 (complementary highlight)
- **Active:** 88x (enabled primary state)
- **Occupied:** 64x (interactive/focused elements)
- **Disabled:** 88x at 24% opacity
- **Surface:** 80x at 8% opacity (content layers)
- **Base-surface:** 8x at 100% (solid container foundation)
- **Base:** 8x at 40% with 24% backdrop blur (translucent surfaces)

### Grouped Component Pattern
Apply 0.5rem (8px) on relative sides creating visual differentiation:
- Example: `1rem 0.5rem 0.5rem 1rem` paired with `0.5rem 1rem 1rem 0.5rem`

## Effects

### Backdrop Blur
- **Default:** 24% provides subtle depth for translucent surfaces
- **Application:** Primarily to base layers at 40% opacity
- **Purpose:** Creates floating panel aesthetic
- **Guidelines:** Avoid excessive blur that compromises legibility or performance
- **Principle:** Effects should enhance hierarchy, not decorate arbitrarily

## Light Scheme Inversion

Light scheme derives from dark scheme through systematic inversion of lightness values.

### Lightness Inversion Mapping
- 100x → 0x
- 88x → 12x
- 80x → 20x
- 64x → 36x
- 8x → 92x
- 0x → 100x

### Inversion Rules
- **Opacity:** Percentages remain unchanged during inversion
- **Hue & Chroma:** Values persist across schemes
- **Color Identity:** Ensures consistency across themes
- **Testing:** Verify sufficient contrast and hierarchy preservation in both schemes

## Usage Guidelines

PMD functions as a flexible guideline rather than rigid specification framework:

### Design Adaptation
- **Contextual Application:** Adapt values contextually while maintaining hierarchical relationships
- **Variable Inheritance:** Leverage mutable variables for rapid theme iteration
- **Scale Selection:** Depends on viewport resolution and perceived object importance
- **Edge Cases:** Bracketed values indicate unlikely standard implementations

### Implementation Philosophy
- **Practicality Over Rigidity:** Allow designers flexibility within systematic constraints
- **Systematic Consistency:** Use variable inheritance to maintain coherence
- **Performance Considerations:** Balance visual requirements with computational efficiency
- **Accessibility:** Ensure sufficient contrast and readability across all implementations

---

*This specification serves as a living document, evolving with practical usage and feedback from the design community.*