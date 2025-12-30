# PMD Hue Offset Toggle Implementation Guide

## Overview

The PMD (Project Minimalist Design) system now includes a **+30° Hue Offset Toggle** that automatically shifts all colors in your palette by +30 degrees, including auxiliary colors. This feature provides a simple way to create color variations while maintaining the design system's consistency.

## What Does the Hue Offset Do?

When enabled, the toggle adds +30° to:

- **Base colors**: All primary, secondary, and accent colors
- **Auxiliary colors**: The +90° offset colors for urgency/warning states
- **Selection colors**: Selection and highlight colors

### Example
- **Base hue**: 345° (default)
- **Aux offset**: +90° = 435° → 75°
- **With +30° offset**: 
  - Base: 345° + 30° = 15°
  - Aux: 75° + 30° = 105°

## Implementation Options

### 1. React/JavaScript Implementation

```typescript
import { createPMDColorSystem, usePMDColorSystem } from './pmd-utils';

// Class-based approach
const colorSystem = createPMDColorSystem(document.documentElement, {
  baseHue: 345,
  auxOffset: 90,
  hueOffsetEnabled: false
});

// Toggle the offset
colorSystem.toggleHueOffset();

// Or enable/disable specifically
colorSystem.enableHueOffset();
colorSystem.disableHueOffset();

// Get current effective colors
const effectiveColors = colorSystem.getEffectiveColors();
```

### 2. React Hook Approach

```typescript
import { usePMDColorSystem } from './pmd-utils';

function MyComponent() {
  const {
    config,
    toggleHueOffset,
    setBaseHue,
    setAuxOffset,
    getEffectiveColors
  } = usePMDColorSystem({
    baseHue: 345,
    auxOffset: 90
  });

  return (
    <div>
      <button onClick={toggleHueOffset}>
        {config.hueOffsetEnabled ? 'Disable' : 'Enable'} +30° Offset
      </button>
      <div style={{ color: 'var(--pmd-primary)' }}>
        Current base hue: {config.baseHue}°
        {config.hueOffsetEnabled && ' (+30° offset active)'}
      </div>
    </div>
  );
}
```

### 3. CSS-Only Implementation

```css
/* Default state - no offset */
:root {
  --pmd-base-hue: 345deg;
  --pmd-effective-base-hue: var(--pmd-base-hue);
}

/* With +30° offset enabled */
.pmd-hue-offset-enabled {
  --pmd-effective-base-hue: calc(var(--pmd-base-hue) + 30deg);
}

/* Toggle class on documentElement */
document.documentElement.classList.toggle('pmd-hue-offset-enabled');
```

### 4. CSS Custom Properties Usage

```css
/* All colors automatically use the effective hue */
.my-component {
  background-color: oklch(0.88 0.056 var(--pmd-effective-base-hue));
  color: var(--pmd-white);
  border: 2px solid oklch(0.88 0.056 var(--pmd-effective-base-hue) / 24%);
}

.urgent-component {
  background-color: oklch(0.88 0.056 calc(var(--pmd-base-hue) + var(--pmd-aux-offset) + 30deg) / 24%);
  border: 2px solid oklch(0.88 0.056 calc(var(--pmd-base-hue) + var(--pmd-aux-offset) + 30deg));
}
```

## Integration with Your Projects

### Tailwind CSS

Add to your `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        pmd: {
          primary: 'var(--pmd-primary)',
          'primary-aux': 'var(--pmd-primary-aux)',
          secondary: 'var(--pmd-secondary)',
          'secondary-aux': 'var(--pmd-secondary-aux)',
          accent: 'var(--pmd-accent)',
          base: 'var(--pmd-base)',
        }
      }
    }
  }
}
```

Usage in JSX:
```jsx
<button className="bg-pmd-primary text-pmd-white border-pmd-primary">
  Primary Button
</button>
<button className="bg-pmd-primary-aux text-pmd-white border-pmd-primary-aux">
  Urgent Action
</button>
```

### Styled Components (React)

```javascript
import styled from 'styled-components';
import { createPMDColorSystem } from './pmd-utils';

const colorSystem = createPMDColorSystem();

export const PrimaryButton = styled.button`
  background-color: ${() => colorSystem.getPMDColorHex('88x')};
  color: white;
  border: 2px solid ${() => colorSystem.getPMDColorHex('88x')};
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    opacity: 0.8;
  }
`;

export const UrgentButton = styled.button`
  background-color: ${() => colorSystem.getPMDColorHex('88x+6')};
  color: white;
  border: 2px solid ${() => colorSystem.getPMDColorHex('88x+6')};
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    opacity: 0.8;
  }
`;
```

### CSS Modules

```css
/* myComponent.module.css */
.primary {
  background-color: var(--pmd-primary);
  color: var(--pmd-white);
  border: 2px solid var(--pmd-primary);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.primary:hover {
  opacity: 0.8;
}

.urgent {
  background-color: var(--pmd-primary-aux);
  color: var(--pmd-white);
  border: 2px solid var(--pmd-primary-aux);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s ease;
}
```

## Quick Reference

### Color Variables

| Variable | Description | Default (345°) | With +30° (15°) |
|----------|-------------|----------------|-----------------|
| `--pmd-primary` | Main brand color | Pink (345°) | Orange (15°) |
| `--pmd-primary-aux` | Urgent/warning | Yellow-green (75°) | Yellow (105°) |
| `--pmd-secondary` | Secondary elements | Pink (345°) | Orange (15°) |
| `--pmd-secondary-aux` | Secondary urgent | Yellow-green (75°) | Yellow (105°) |
| `--pmd-accent` | Action/links | Pink (345°) | Orange (15°) |
| `--pmd-base` | Background/frames | Dark (345°) | Dark (15°) |

### Utility Functions

```typescript
// Quick toggle
toggleHueOffset(); // Returns boolean (new state)

// Get current state
const state = getEffectivePMDColors();
console.log(state);
// {
//   base: { hue: 15, colors: {...} },
//   aux: { hue: 105, colors: {...} },
//   config: { baseHue: 345, auxOffset: 90, hueOffsetEnabled: true }
// }

// Set specific values
colorSystem.setBaseHue(200); // Cool blue
colorSystem.setAuxOffset(120); // Wider aux separation
colorSystem.enableHueOffset(); // Activate +30° shift
```

## Best Practices

1. **Use the React hook** when possible for reactive updates
2. **CSS custom properties** work well for static styling
3. **Class-based toggling** is simplest for global changes
4. **Always test both states** (enabled/disabled) in your UI
5. **Consider accessibility** - ensure sufficient contrast in both states
6. **Document usage** in your team's design guidelines

## Troubleshooting

### Colors Not Updating
- Check that the `pmd-hue-offset-enabled` class is properly applied
- Verify CSS custom properties are being used in your styles
- Ensure JavaScript execution order (DOM must be ready)

### TypeScript Errors
- Import types from `./pmd-utils`
- Check that your element extends `HTMLElement`
- Verify color type names match the `PMD_COLORS` keys

### Performance
- Use the React hook for frequent updates
- CSS custom properties are GPU-accelerated
- Avoid excessive toggle calls in animations

## Example: Complete Implementation

See the live demo in `/src/App.tsx` for a complete working example with:
- Toggle switch UI
- Real-time color preview
- Hex value copying
- Responsive design
- All PMD color variations

This demonstrates how the hue offset toggle integrates seamlessly with your existing PMD design system while providing an intuitive interface for color management.