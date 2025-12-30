/**
 * PMD Design System Utilities
 * ==========================
 * TypeScript utilities for controlling the PMD color system with hue offset toggle
 */

export interface PMDHueConfig {
  baseHue: number;
  auxOffset: number;
  hueOffsetEnabled: boolean;
}

export interface PMDColor {
  l: number;
  c: number;
  h: number;
  opacity?: number;
}

/**
 * PMD Color System Class
 * Provides methods to control and compute PMD colors with hue offset
 */
export class PMDColorSystem {
  private baseHue: number;
  private auxOffset: number;
  private hueOffsetEnabled: boolean;
  private element: HTMLElement;

  constructor(
    element: HTMLElement = document.documentElement,
    config: Partial<PMDHueConfig> = {}
  ) {
    this.element = element;
    this.baseHue = config.baseHue ?? 0;
    this.auxOffset = config.auxOffset ?? 90;
    this.hueOffsetEnabled = config.hueOffsetEnabled ?? false;
    this.applyToDOM();
  }

  /**
   * Get the effective base hue (with +30deg offset if enabled)
   */
  getEffectiveBaseHue(): number {
    return this.hueOffsetEnabled ? (this.baseHue + 30) % 360 : this.baseHue;
  }

  /**
   * Get the effective auxiliary hue
   */
  getEffectiveAuxHue(): number {
    const auxHue = (this.baseHue + this.auxOffset) % 360;
    return this.hueOffsetEnabled ? (auxHue + 30) % 360 : auxHue;
  }

  /**
   * Set the base hue (0-360 degrees)
   */
  setBaseHue(hue: number): void {
    this.baseHue = ((hue % 360) + 360) % 360;
    this.applyToDOM();
  }

  /**
   * Get the current base hue
   */
  getBaseHue(): number {
    return this.baseHue;
  }

  /**
   * Set the auxiliary offset (degrees)
   */
  setAuxOffset(offset: number): void {
    this.auxOffset = offset;
    this.applyToDOM();
  }

  /**
   * Get the current auxiliary offset
   */
  getAuxOffset(): number {
    return this.auxOffset;
  }

  /**
   * Toggle the +30deg hue offset
   */
  toggleHueOffset(): boolean {
    this.hueOffsetEnabled = !this.hueOffsetEnabled;
    this.applyToDOM();
    return this.hueOffsetEnabled;
  }

  /**
   * Enable the +30deg hue offset
   */
  enableHueOffset(): void {
    this.hueOffsetEnabled = true;
    this.applyToDOM();
  }

  /**
   * Disable the +30deg hue offset
   */
  disableHueOffset(): void {
    this.hueOffsetEnabled = false;
    this.applyToDOM();
  }

  /**
   * Check if hue offset is enabled
   */
  isHueOffsetEnabled(): boolean {
    return this.hueOffsetEnabled;
  }

  /**
   * Get the current configuration
   */
  getConfig(): PMDHueConfig {
    return {
      baseHue: this.baseHue,
      auxOffset: this.auxOffset,
      hueOffsetEnabled: this.hueOffsetEnabled
    };
  }

  /**
   * Apply configuration to the DOM
   */
  private applyToDOM(): void {
    this.element.style.setProperty('--pmd-base-hue', `${this.baseHue}deg`);
    this.element.style.setProperty('--pmd-aux-offset', `${this.auxOffset}deg`);
    
    if (this.hueOffsetEnabled) {
      this.element.classList.add('pmd-hue-offset-enabled');
    } else {
      this.element.classList.remove('pmd-hue-offset-enabled');
    }
  }

  /**
   * Convert OKLCH to RGB
   */
  static oklchToRgb(l: number, c: number, h: number): [number, number, number] {
    const hRad = (h * Math.PI) / 180;
    const a = c * Math.cos(hRad);
    const b = c * Math.sin(hRad);
    
    const l_ = l + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = l - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = l - 0.0894841775 * a - 1.2914855480 * b;
    
    const l3 = l_ * l_ * l_;
    const m3 = m_ * m_ * m_;
    const s3 = s_ * s_ * s_;
    
    let r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3;
    let g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3;
    let bl = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3;
    
    const gammaCorrect = (c: number) => {
      const abs = Math.abs(c);
      if (abs > 0.0031308) {
        return Math.sign(c) * (1.055 * Math.pow(abs, 1/2.4) - 0.055);
      }
      return 12.92 * c;
    };
    
    r = gammaCorrect(r);
    g = gammaCorrect(g);
    bl = gammaCorrect(bl);
    
    r = Math.max(0, Math.min(1, r));
    g = Math.max(0, Math.min(1, g));
    bl = Math.max(0, Math.min(1, bl));
    
    return [
      Math.round(r * 255),
      Math.round(g * 255),
      Math.round(bl * 255)
    ];
  }

  /**
   * Convert RGB to hex
   */
  static rgbToHex(r: number, g: number, b: number): string {
    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
  }

  /**
   * Get PMD color as hex string
   */
  getPMDColorHex(colorType: keyof typeof PMD_COLORS): string {
    const color = PMD_COLORS[colorType];
    const hue = (color as any).aux ? this.getEffectiveAuxHue() : this.getEffectiveBaseHue();
    const rgb = PMDColorSystem.oklchToRgb(color.l, color.c, hue);
    return PMDColorSystem.rgbToHex(rgb[0], rgb[1], rgb[2]);
  }

  /**
   * Subscribe to configuration changes
   */
  onChange(callback: (config: PMDHueConfig) => void): () => void {
    const observer = new MutationObserver(() => {
      callback(this.getConfig());
    });
    observer.observe(this.element, {
      attributes: true,
      attributeFilter: ['style', 'class']
    });
    return () => observer.disconnect();
  }
}

/**
 * PMD Color Definitions
 */
export const PMD_COLORS = {
  white: { l: 1, c: 0, h: 0, aux: false },
  '96x': { l: 0.96, c: 0.016, h: 0, aux: false },
  '88x': { l: 0.88, c: 0.056, h: 0, aux: false },
  '88x+6': { l: 0.88, c: 0.056, h: 0, aux: true },
  '80x': { l: 0.8, c: 0.1, h: 0, aux: false },
  '80x+6': { l: 0.8, c: 0.1, h: 0, aux: true },
  '76x': { l: 0.76, c: 0.12, h: 0, aux: false },
  '8x': { l: 0.2, c: 0.032, h: 0, aux: false },
  black: { l: 0, c: 0, h: 0, aux: false }
} as const;

/**
 * Create a PMD color system instance
 */
export function createPMDColorSystem(
  element?: HTMLElement,
  config?: Partial<PMDHueConfig>
): PMDColorSystem {
  return new PMDColorSystem(element, config);
}

/**
 * Quick toggle function for the hue offset
 */
export function toggleHueOffset(element: HTMLElement = document.documentElement): boolean {
  const system = new PMDColorSystem(element);
  return system.toggleHueOffset();
}

/**
 * Get current effective colors
 */
export function getEffectivePMDColors(element: HTMLElement = document.documentElement) {
  const system = new PMDColorSystem(element);
  const config = system.getConfig();
  
  return {
    base: {
      hue: system.getEffectiveBaseHue(),
      colors: {
        '88x': system.getPMDColorHex('88x'),
        '80x': system.getPMDColorHex('80x'),
        '76x': system.getPMDColorHex('76x'),
        '8x': system.getPMDColorHex('8x'),
        '96x': system.getPMDColorHex('96x')
      }
    },
    aux: {
      hue: system.getEffectiveAuxHue(),
      colors: {
        '88x+6': system.getPMDColorHex('88x+6'),
        '80x+6': system.getPMDColorHex('80x+6')
      }
    },
    config
  };
}

/**
 * React Hook for PMD Color System
 * Note: This requires React to be imported in your project
 */
export function usePMDColorSystem(config?: Partial<PMDHueConfig>) {
  const [system] = useState(() => new PMDColorSystem(document.documentElement, config));
  const [configState, setConfigState] = useState(() => system.getConfig());

  useEffect(() => {
    const unsubscribe = system.onChange((newConfig) => {
      setConfigState(newConfig);
    });
    return unsubscribe;
  }, [system]);

  return {
    system,
    config: configState,
    setBaseHue: (hue: number) => system.setBaseHue(hue),
    setAuxOffset: (offset: number) => system.setAuxOffset(offset),
    toggleHueOffset: () => system.toggleHueOffset(),
    enableHueOffset: () => system.enableHueOffset(),
    disableHueOffset: () => system.disableHueOffset(),
    getEffectiveColors: () => getEffectivePMDColors()
  };
}

// TypeScript type imports for React hook
// In your actual project, import these from React:
// import { useState, useEffect } from 'react';
declare function useState<T>(initial: T | (() => T)): [T, (value: T) => void];
declare function useEffect(effect: () => void | (() => void), deps?: any[]): void;