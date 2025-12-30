import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

function oklchToRgb(l: number, c: number, h: number): [number, number, number] {
  // Convert OKLCH to OKLAB
  const hRad = (h * Math.PI) / 180;
  const a = c * Math.cos(hRad);
  const b = c * Math.sin(hRad);
  
  // OKLAB to linear RGB
  const l_ = l + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = l - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = l - 0.0894841775 * a - 1.2914855480 * b;
  
  const l3 = l_ * l_ * l_;
  const m3 = m_ * m_ * m_;
  const s3 = s_ * s_ * s_;
  
  let r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3;
  let g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3;
  let bl = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3;
  
  // Gamma correction
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
  
  // Clamp to sRGB
  r = Math.max(0, Math.min(1, r));
  g = Math.max(0, Math.min(1, g));
  bl = Math.max(0, Math.min(1, bl));
  
  return [
    Math.round(r * 255),
    Math.round(g * 255),
    Math.round(bl * 255)
  ];
}

function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
}

interface ColorSwatchProps {
  label: string;
  l: number;
  c: number;
  h: number;
  opacity?: number;
  baseHue: number;
  primary?: boolean;
}

function ColorSwatch({ label, l, c, h, opacity = 100, baseHue, primary: _ }: ColorSwatchProps) {
  const [copied, setCopied] = useState(false);
  const rgb = oklchToRgb(l, c, h);
  const hex = rgbToHex(rgb[0], rgb[1], rgb[2]);
  const hexWithAlpha = opacity < 100 ? hex + Math.round(opacity * 2.55).toString(16).padStart(2, '0').toUpperCase() : hex;
  
  const handleCopy = () => {
    navigator.clipboard.writeText(hexWithAlpha);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const primaryRgb = oklchToRgb(0.88, 0.056, baseHue);
  const primaryHex = rgbToHex(primaryRgb[0], primaryRgb[1], primaryRgb[2]);
  const hoverRgb = oklchToRgb(0.8, 0.1, baseHue);
  const hoverHex = rgbToHex(hoverRgb[0], hoverRgb[1], hoverRgb[2]);
  
  // Auto-invert text color based on background
  const getContrastColor = (hexColor: string) => {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128 ? '#000000' : '#FFFFFF';
  };
  
  const swatchTextColor = getContrastColor(hex);
  
  return (
    <div 
      className="flex items-center gap-2 p-2 rounded-2xl transition-colors"
      style={{
        '--hover-bg': hoverHex + '14'
      } as React.CSSProperties}
      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg)'}
      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
    >
      <div 
        className="w-12 h-12 rounded-2xl flex-shrink-0 relative"
        style={{ 
          backgroundColor: hex,
          opacity: opacity / 100,
          border: `2px solid ${getContrastColor(hex) === '#FFFFFF' ? '#FFFFFF33' : '#00000033'}`
        }}
      >
        <div 
          className="absolute inset-0 flex items-center justify-center text-xs font-mono"
          style={{ color: getContrastColor(hex) }}
        >
          {Math.round(opacity)}%
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-xs" style={{ color: primaryHex }}>{label}</div>
        <div className="text-xs font-mono" style={{ color: rgbToHex(...oklchToRgb(0.6, 0.08, baseHue)) }}>
          oklch({l} {c.toFixed(3)} {h})
        </div>
        <div className="text-xs font-mono" style={{ color: rgbToHex(...oklchToRgb(0.5, 0.06, baseHue)) }}>{hexWithAlpha}</div>
      </div>
      <button
        onClick={handleCopy}
        className="p-1 rounded-2xl transition-colors"
        style={{
          color: rgbToHex(...oklchToRgb(0.5, 0.06, baseHue))
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = hoverHex + '14'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        {copied ? <Check className="w-3 h-3" style={{ color: rgbToHex(...oklchToRgb(0.8, 0.1, baseHue + 90)) }} /> : <Copy className="w-3 h-3" />}
      </button>
    </div>
  );
}

export default function PMDColorConverter() {
  const [baseHue, setBaseHue] = useState(0);
  const [auxOffset, setAuxOffset] = useState(90);
  const [baseHueInput, setBaseHueInput] = useState('0');
  const [auxOffsetInput, setAuxOffsetInput] = useState('90');
  const [hueOffsetEnabled, setHueOffsetEnabled] = useState(false);
  
  // Apply +30deg offset when enabled
  const effectiveBaseHue = hueOffsetEnabled ? (baseHue + 30) % 360 : baseHue;
  const effectiveAuxOffset = hueOffsetEnabled ? (baseHue + auxOffset + 30) % 360 : (baseHue + auxOffset) % 360;
  
  // Auto-invert text color based on background
  const getContrastColor = (hexColor: string) => {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128 ? '#000000' : '#FFFFFF';
  };
  
  // Auto-invert text color for any background color
  const getAutoInvertText = (backgroundColor: string, darkText?: string, lightText?: string) => {
    const r = parseInt(backgroundColor.slice(1, 3), 16);
    const g = parseInt(backgroundColor.slice(3, 5), 16);
    const b = parseInt(backgroundColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    if (brightness > 128) {
      // Light background - use dark text
      return darkText || '#000000';
    } else {
      // Dark background - use light text
      return lightText || '#FFFFFF';
    }
  };
  
  // Auto-invert border color
  const getAutoInvertBorder = (backgroundColor: string) => {
    const r = parseInt(backgroundColor.slice(1, 3), 16);
    const g = parseInt(backgroundColor.slice(3, 5), 16);
    const b = parseInt(backgroundColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    if (brightness > 128) {
      // Light background - use darker border
      return '#00000033';
    } else {
      // Dark background - use lighter border
      return '#FFFFFF33';
    }
  };
  
  // Get text color based on theme (8x for dark, 88x for light)
  const getThemeTextColor = (backgroundColor: string, darkText?: string, lightText?: string) => {
    const r = parseInt(backgroundColor.slice(1, 3), 16);
    const g = parseInt(backgroundColor.slice(3, 5), 16);
    const b = parseInt(backgroundColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    if (brightness > 128) {
      // Light background - use dark text (8x color)
      const darkRgb = oklchToRgb(0.2, 0.032, effectiveBaseHue);
      const darkHex = rgbToHex(darkRgb[0], darkRgb[1], darkRgb[2]);
      return darkText || darkHex;
    } else {
      // Dark background - use light text (88x color)
      const lightRgb = oklchToRgb(0.88, 0.056, effectiveBaseHue);
      const lightHex = rgbToHex(lightRgb[0], lightRgb[1], lightRgb[2]);
      return lightText || lightHex;
    }
  };
  
  // Get inverted text color for accent backgrounds (on-accent)
  const getOnAccentText = (accentBackgroundColor: string) => {
    const r = parseInt(accentBackgroundColor.slice(1, 3), 16);
    const g = parseInt(accentBackgroundColor.slice(3, 5), 16);
    const b = parseInt(accentBackgroundColor.slice(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    if (brightness > 128) {
      // Light accent background - use dark text (8x color)
      const darkRgb = oklchToRgb(0.2, 0.032, effectiveBaseHue);
      return rgbToHex(darkRgb[0], darkRgb[1], darkRgb[2]);
    } else {
      // Dark accent background - use light text (88x color)
      const lightRgb = oklchToRgb(0.88, 0.056, effectiveBaseHue);
      return rgbToHex(lightRgb[0], lightRgb[1], lightRgb[2]);
    }
  };
  
  const commitHueChange = (value: string) => {
    const num = parseFloat(value);
    if (!isNaN(num)) {
      const normalized = ((num % 360) + 360) % 360;
      setBaseHue(normalized);
      setBaseHueInput(normalized.toString());
    } else if (value === '') {
      setBaseHue(0);
      setBaseHueInput('0');
    }
  };
  
  const toggleHueOffset = () => {
    setHueOffsetEnabled(!hueOffsetEnabled);
  };
  
  const commitAuxChange = (value: string) => {
    const num = parseFloat(value);
    if (!isNaN(num)) {
      setAuxOffset(num);
      setAuxOffsetInput(num.toString());
    } else if (value === '') {
      setAuxOffset(0);
      setAuxOffsetInput('0');
    }
  };
  
  const pmdColors = [
    { label: '100x (White)', l: 1, c: 0, h: 0, opacities: [100, 32] },
    { label: '96x (Selection)', l: 0.96, c: 0.016, h: effectiveBaseHue, opacities: [100] },
    { label: '88x (Primary)', l: 0.88, c: 0.056, h: effectiveBaseHue, opacities: [100, 48, 24] },
    { label: '88x+6 (PrimaryAux)', l: 0.88, c: 0.056, h: effectiveAuxOffset, opacities: [100, 24] },
    { label: '80x (Secondary)', l: 0.8, c: 0.1, h: effectiveBaseHue, opacities: [100, 48, 12, 8] },
    { label: '80x+6 (SecondaryAux)', l: 0.8, c: 0.1, h: effectiveAuxOffset, opacities: [100, 48, 12, 8] },
    { label: '76x (Accent)', l: 0.76, c: 0.12, h: effectiveBaseHue, opacities: [100, 80] },
    { label: '8x (Base)', l: 0.2, c: 0.032, h: effectiveBaseHue, opacities: [100, 80, 64, 40] },
    { label: '0x (Black)', l: 0, c: 0, h: 0, opacities: [100, 80, 64, 40] },
  ];
  
  // PMD color variables
  const baseRgb = oklchToRgb(0.2, 0.032, effectiveBaseHue);
  const surfaceRgb = oklchToRgb(0.8, 0.1, effectiveBaseHue);
  const primaryRgb = oklchToRgb(0.88, 0.056, effectiveBaseHue);
  const secondaryRgb = oklchToRgb(0.8, 0.1, effectiveBaseHue);
  const accentRgb = oklchToRgb(0.76, 0.12, effectiveBaseHue);
  const auxRgb = oklchToRgb(0.88, 0.056, effectiveAuxOffset);
  
  const baseColor = rgbToHex(baseRgb[0], baseRgb[1], baseRgb[2]);
  const surfaceColor = rgbToHex(surfaceRgb[0], surfaceRgb[1], surfaceRgb[2]);
  const primaryColor = rgbToHex(primaryRgb[0], primaryRgb[1], primaryRgb[2]);
  const secondaryColor = rgbToHex(secondaryRgb[0], secondaryRgb[1], secondaryRgb[2]);
  const accentColor = rgbToHex(accentRgb[0], accentRgb[1], accentRgb[2]);
  const auxColor = rgbToHex(auxRgb[0], auxRgb[1], auxRgb[2]);
  
  return (
    <div 
      className="min-h-screen p-4"
      style={{ backgroundColor: baseColor }}
    >
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div 
          className="rounded-2xl p-6 mb-6"
          style={{ 
            backgroundColor: baseColor + 'A6',
            backdropFilter: 'blur(24px)',
            border: `2px solid ${primaryColor}3D`
          }}
        >
          <h1 className="text-2xl font-bold mb-2 font-fredoka" style={{ color: primaryColor }}>
            PMD OKLCH Color Converter
          </h1>
          <p className="text-sm mb-4 font-medium" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
            Visualize your Project Minimalist Design palette with OKLCH values
          </p>
          
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2 font-medium" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
                Base Hue (degrees)
              </label>
              <input
                type="number"
                min="0"
                max="360"
                value={baseHueInput}
                onChange={(e) => setBaseHueInput(e.target.value)}
                onBlur={(e) => commitHueChange((e.target as HTMLInputElement).value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    commitHueChange((e.target as HTMLInputElement).value);
                    (e.target as HTMLInputElement).blur();
                  }
                }}
                className="w-full px-3 py-2 rounded-2xl focus:outline-none"
                style={{
                  backgroundColor: surfaceColor + '14',
                  color: primaryColor,
                  border: `2px solid ${primaryColor}3D`
                }}
                placeholder="0-360"
              />
              <div className="text-xs mt-1" style={{ color: accentColor }}>0-360 degrees</div>
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2 font-medium" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
                Aux Hue Offset (degrees)
              </label>
              <input
                type="number"
                min="0"
                max="360"
                value={auxOffsetInput}
                onChange={(e) => setAuxOffsetInput(e.target.value)}
                onBlur={(e) => commitAuxChange((e.target as HTMLInputElement).value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    commitAuxChange((e.target as HTMLInputElement).value);
                    (e.target as HTMLInputElement).blur();
                  }
                }}
                className="w-full px-3 py-2 rounded-2xl focus:outline-none"
                style={{
                  backgroundColor: surfaceColor + '14',
                  color: primaryColor,
                  border: `2px solid ${primaryColor}3D`
                }}
                placeholder="0-360"
              />
              <div className="text-xs mt-1 font-nerd" style={{ color: getThemeTextColor(baseColor + 'A6', accentColor) }}>0-360 degrees</div>
            </div>
          </div>
          
          {/* Hue Offset Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={toggleHueOffset}
              className="relative inline-flex h-6 w-11 items-center rounded-2xl transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2"
              style={{
                backgroundColor: hueOffsetEnabled ? accentColor : surfaceColor + '3D'
              }}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-2xl transition-transform ${
                  hueOffsetEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
                style={{
                  backgroundColor: hueOffsetEnabled ? primaryColor : accentColor
                }}
              />
            </button>
            <div>
              <div className="text-sm font-medium font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
                +30° Hue Offset {hueOffsetEnabled ? 'ON' : 'OFF'}
              </div>
              <div className="text-xs font-medium" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
                Automatically shift all colors by +30° including aux
              </div>
            </div>
            {hueOffsetEnabled && (
              <div className="ml-auto text-xs p-2 rounded-2xl font-nerd" style={{ backgroundColor: accentColor + '14', color: getThemeTextColor(accentColor + '14', accentColor) }}>
                Base: {baseHue}° → {effectiveBaseHue}° • Aux: {effectiveAuxOffset}°
              </div>
            )}
          </div>
        </div>
        
        {/* Two Column Layout */}
        <div className="grid grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Color Usage Demo */}
            <div 
              className="rounded-lg p-4"
              style={{ 
                backgroundColor: baseColor + 'A6',
                backdropFilter: 'blur(24px)',
                border: `2px solid ${primaryColor}3D`
              }}
            >
              <h2 className="text-lg font-semibold mb-3 font-fredoka-semibold" style={{ color: primaryColor }}>
                Color Usage Demo
              </h2>
              <p className="text-xs mb-3 font-medium" style={{ color: getThemeTextColor(baseColor + 'A6') }}>
                Primary (88x) • Aux (+{hueOffsetEnabled ? auxOffset + 30 : auxOffset}°) • Accent (76x)
                {hueOffsetEnabled && ' • +30° offset'}
              </p>
              
              <div className="grid grid-cols-1 gap-3">
                <div className="space-y-2">
                  <div className="text-xs font-medium font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Primary State</div>
                  
                  <div 
                    className="p-2 rounded"
                    style={{ 
                      backgroundColor: surfaceColor + '14',
                      border: `2px solid ${primaryColor}3D`
                    }}
                  >
                    <div className="text-xs font-medium" style={{ color: primaryColor }}>Temperature</div>
                    <div className="text-lg font-bold" style={{ color: primaryColor }}>72°F</div>
                  </div>
                  
                  <div 
                    className="p-2 rounded"
                    style={{ 
                      backgroundColor: surfaceColor + '14',
                      border: `2px solid ${primaryColor}3D`
                    }}
                  >
                    <div className="text-xs" style={{ color: secondaryColor }}>System status</div>
                    <div className="text-xs font-medium" style={{ color: primaryColor }}>Active</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-xs font-medium" style={{ color: auxColor }}>Aux/Urgent State</div>
                  
                  <div 
                    className="p-2 rounded"
                    style={{ 
                      backgroundColor: auxColor + '14',
                      border: `2px solid ${auxColor}3D`
                    }}
                  >
                    <div className="text-xs font-medium" style={{ color: auxColor }}>Temperature</div>
                    <div className="text-lg font-bold" style={{ color: auxColor }}>95°F</div>
                  </div>
                  
                  <div 
                    className="p-2 rounded"
                    style={{ 
                      backgroundColor: auxColor + '14',
                      border: `2px solid ${auxColor}3D`
                    }}
                  >
                    <div className="text-xs" style={{ color: rgbToHex(...oklchToRgb(0.8, 0.1, effectiveAuxOffset)) }}>
                      System status
                    </div>
                    <div className="text-xs font-medium" style={{ color: auxColor }}>Warning</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-xs font-medium font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Accent/Action</div>
                  
                  <button
                    className="w-full p-2 rounded-2xl transition-opacity"
                    style={{ 
                      backgroundColor: accentColor + 'FF',
                      border: `2px solid ${accentColor}`,
                      color: getOnAccentText(accentColor + 'FF'),
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => (e.target as HTMLButtonElement).style.opacity = '0.8'}
                    onMouseLeave={(e) => (e.target as HTMLButtonElement).style.opacity = '1'}
                  >
                    <div className="text-xs font-medium">Delete File</div>
                  </button>
                  
                  <div 
                    className="p-2 rounded"
                    style={{ 
                      backgroundColor: surfaceColor + '14',
                      border: `2px solid ${primaryColor}3D`
                    }}
                  >
                    <div className="text-xs" style={{ color: secondaryColor }}>
                      Learn more at{' '}
                      <span style={{ color: accentColor, cursor: 'pointer' }}>docs.example.com</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Compact Color Palette */}
            <div 
              className="rounded-lg p-4"
              style={{ 
                backgroundColor: baseColor + 'A6',
                backdropFilter: 'blur(24px)',
                border: `2px solid ${primaryColor}3D`
              }}
            >
              <h2 className="text-lg font-semibold mb-3" style={{ color: primaryColor }}>
                Color Palette
              </h2>
              <div className="space-y-3">
                {pmdColors.map((color, idx) => (
                  <div key={idx}>
                    <ColorSwatch
                      label={color.label}
                      l={color.l}
                      c={color.c}
                      h={color.h}
                      opacity={100}
                      baseHue={baseHue}
                      primary={true}
                    />
                    {color.opacities.length > 1 && (
                      <div className="ml-20 mt-2 space-y-1">
                        {color.opacities.slice(1).map((opacity) => (
                          <ColorSwatch
                            key={opacity}
                            label={`${opacity}%`}
                            l={color.l}
                            c={color.c}
                            h={color.h}
                            opacity={opacity}
                            baseHue={baseHue}
                            primary={false}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Right Column */}
          <div className="space-y-6">
        
            {/* Full Component Preview */}
            <div 
              className="rounded-lg p-4"
              style={{ 
                backgroundColor: baseColor + 'A6',
                backdropFilter: 'blur(24px)',
                border: `2px solid ${primaryColor}3D`
              }}
            >
              <h2 className="text-lg font-semibold mb-3" style={{ color: primaryColor }}>
                Component Preview
              </h2>
              <p className="text-xs mb-4" style={{ color: secondaryColor }}>
                PMD colors in real UI components
              </p>
              
              {/* Compact Navigation */}
              <div className="mb-4">
                <div className="text-xs font-medium mb-2 font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Navigation</div>
                <div 
                  className="flex items-center gap-2 p-2 rounded"
                  style={{ 
                    backgroundColor: surfaceColor + '14', 
                    border: `2px solid ${getAutoInvertBorder(surfaceColor + '14')}`,
                    color: getThemeTextColor(surfaceColor + '14')
                  }}
                >
                  <div className="text-xs font-medium font-fredoka-semibold" style={{ color: getContrastColor(baseColor) }}>PMD</div>
                  <div className="flex-1" />
                  <button 
                    className="px-2 py-1 rounded-2xl text-xs font-medium transition-opacity font-medium"
                    style={{ 
                      backgroundColor: primaryColor,
                      color: getContrastColor(primaryColor),
                      border: `2px solid ${primaryColor}`
                    }}
                    onMouseEnter={(e) => (e.target as HTMLButtonElement).style.opacity = '0.8'}
                    onMouseLeave={(e) => (e.target as HTMLButtonElement).style.opacity = '1'}
                  >
                    Home
                  </button>
                  <button 
                    className="px-2 py-1 rounded-2xl text-xs font-medium transition-opacity font-medium"
                    style={{ 
                      backgroundColor: 'transparent',
                      color: getContrastColor(baseColor),
                      border: `2px solid ${getAutoInvertBorder(surfaceColor + '14')}`
                    }}
                    onMouseEnter={(e) => (e.target as HTMLButtonElement).style.backgroundColor = surfaceColor + '14'}
                    onMouseLeave={(e) => (e.target as HTMLButtonElement).style.backgroundColor = 'transparent'}
                  >
                    Docs
                  </button>
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Form & Buttons */}
                <div>
                  <div className="text-xs font-medium mb-2 font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Forms & Buttons</div>
                  
                  <div className="space-y-2">
                    <input
                      type="email"
                      className="w-full px-2 py-1 rounded-2xl text-xs focus:outline-none placeholder-opacity-60"
                      style={{
                        backgroundColor: surfaceColor + '14',
                        color: primaryColor,
                        border: `2px solid ${primaryColor}24`
                      }}
                      placeholder="email@example.com"
                    />
                    
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        className="p-2 rounded-2xl text-xs font-medium transition-opacity"
                        style={{ 
                          backgroundColor: primaryColor,
                          color: getContrastColor(primaryColor),
                          border: `2px solid ${primaryColor}`
                        }}
                        onMouseEnter={(e) => (e.target as HTMLButtonElement).style.opacity = '0.8'}
                        onMouseLeave={(e) => (e.target as HTMLButtonElement).style.opacity = '1'}
                      >
                        Primary
                      </button>
                      
                      <button
                        className="p-2 rounded-2xl text-xs font-medium transition-opacity"
                        style={{ 
                          backgroundColor: auxColor,
                          color: getContrastColor(auxColor),
                          border: `2px solid ${auxColor}`
                        }}
                        onMouseEnter={(e) => (e.target as HTMLButtonElement).style.opacity = '0.8'}
                        onMouseLeave={(e) => (e.target as HTMLButtonElement).style.opacity = '1'}
                      >
                        Urgent
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Status & Alerts */}
                <div>
                  <div className="text-xs font-medium mb-2 font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Status & Alerts</div>
                  
                  <div className="space-y-2">
                    <div 
                      className="flex items-center gap-2 p-2 rounded"
                      style={{ 
                        backgroundColor: primaryColor + '14', 
                        border: `2px solid ${getAutoInvertBorder(primaryColor + '14')}`,
                        color: getAutoInvertText(primaryColor + '14', primaryColor, primaryColor)
                      }}
                    >
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: primaryColor }} />
                      <span className="text-xs">Active</span>
                    </div>
                    
                    <div 
                      className="flex items-center gap-2 p-2 rounded"
                      style={{ 
                        backgroundColor: auxColor + '14', 
                        border: `2px solid ${getAutoInvertBorder(auxColor + '14')}`,
                        color: getAutoInvertText(auxColor + '14', auxColor, auxColor)
                      }}
                    >
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: auxColor }} />
                      <span className="text-xs">Warning</span>
                    </div>
                    
                    <div 
                      className="p-2 rounded-2xl"
                      style={{ 
                        backgroundColor: accentColor + '14',
                        border: `2px solid ${accentColor}`,
                        color: getThemeTextColor(accentColor + '14')
                      }}
                    >
                      <div className="text-xs font-medium" style={{ color: accentColor }}>⚠️ Alert</div>
                      <div className="text-xs" style={{ color: getThemeTextColor(accentColor + '14', secondaryColor) }}>System notification</div>
                    </div>
                  </div>
                </div>
                
                {/* Card Example */}
                <div>
                  <div className="text-xs font-medium mb-2 font-semibold" style={{ color: getThemeTextColor(baseColor + 'A6') }}>Card Component</div>
                  
                  <div 
                    className="p-3 rounded-2xl"
                    style={{ 
                      backgroundColor: surfaceColor + '14',
                      border: `2px solid ${getAutoInvertBorder(surfaceColor + '14')}`,
                      color: getAutoInvertText(surfaceColor + '14', primaryColor, secondaryColor)
                    }}
                  >
                    <div className="text-xs font-medium mb-1">Settings</div>
                    <div className="text-xs mb-2">Configure preferences</div>
                    <div className="flex gap-2">
                      <button
                        className="px-2 py-1 rounded-2xl text-xs transition-opacity"
                        style={{ 
                          backgroundColor: primaryColor,
                          color: getContrastColor(primaryColor),
                          border: `2px solid ${primaryColor}`
                        }}
                        onMouseEnter={(e) => (e.target as HTMLButtonElement).style.opacity = '0.8'}
                        onMouseLeave={(e) => (e.target as HTMLButtonElement).style.opacity = '1'}
                      >
                        Save
                      </button>
                      <button
                        className="px-2 py-1 rounded-2xl text-xs transition-opacity"
                        style={{ 
                          backgroundColor: 'transparent',
                          color: getAutoInvertText(surfaceColor + '14', secondaryColor, secondaryColor),
                          border: `2px solid ${getAutoInvertBorder(surfaceColor + '14')}`
                        }}
                        onMouseEnter={(e) => (e.target as HTMLButtonElement).style.backgroundColor = surfaceColor + '14'}
                        onMouseLeave={(e) => (e.target as HTMLButtonElement).style.backgroundColor = 'transparent'}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-4 text-center text-xs" style={{ color: accentColor }}>
          Click the copy icon to copy hex values to clipboard
        </div>
      </div>
    </div>
  );
}
