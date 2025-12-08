import React, { useState, useEffect, useRef } from 'react';
import { Play, Plus, Trash2, Volume2, Square, GripVertical, Keyboard } from 'lucide-react';

const ChordProgressionApp = () => {
  const [progression, setProgression] = useState([]);
  const [selectedRoot, setSelectedRoot] = useState('C');
  const [selectedQuality, setSelectedQuality] = useState('major');
  const [volume, setVolume] = useState(0.5);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentChordIndex, setCurrentChordIndex] = useState(-1);
  const [bpm, setBpm] = useState(120);
  const [timeSignature, setTimeSignature] = useState('4/4');
  const [loop, setLoop] = useState(false);
  const [clickedChord, setClickedChord] = useState(null);
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [holdingChord, setHoldingChord] = useState(null);
  const [showKeybinds, setShowKeybinds] = useState(false);
  const audioContextRef = useRef(null);
  const stopPlaybackRef = useRef(false);
  const holdTimerRef = useRef(null);
  const holdIntervalRef = useRef(null);

  const presets = {
    'Dramatic': [
      { root: 'A', quality: 'minor' },
      { root: 'F', quality: 'major' },
      { root: 'C', quality: 'maj7' },
      { root: 'G', quality: 'major' },
      { root: 'E', quality: 'minor' },
      { root: 'D', quality: 'min7' },
      { root: 'E', quality: 'sus4' },
      { root: 'E', quality: 'major' }
    ],
    'Emotional': [
      { root: 'C', quality: 'maj9' },
      { root: 'A', quality: 'min9' },
      { root: 'F', quality: 'maj7' },
      { root: 'G', quality: 'sus4' },
      { root: 'G', quality: 'dom7' }
    ],
    'Epic': [
      { root: 'D', quality: 'minor' },
      { root: 'A#', quality: 'maj7' },
      { root: 'C', quality: 'major' },
      { root: 'A', quality: 'minor' },
      { root: 'G', quality: 'min7' },
      { root: 'A', quality: 'dom7' }
    ],
    'Ethereal': [
      { root: 'C', quality: 'maj7' },
      { root: 'E', quality: 'min9' },
      { root: 'A', quality: 'min7' },
      { root: 'F', quality: 'maj9' },
      { root: 'G', quality: 'sus4' }
    ],
    'Tense': [
      { root: 'C', quality: 'dim7' },
      { root: 'D', quality: 'min7' },
      { root: 'G', quality: '7sharp9' },
      { root: 'C', quality: 'maj7' }
    ],
    'Melancholic': [
      { root: 'A', quality: 'minor' },
      { root: 'F', quality: 'maj7' },
      { root: 'C', quality: 'major' },
      { root: 'G', quality: 'minor' },
      { root: 'D', quality: 'min7' },
      { root: 'E', quality: 'dom7' }
    ],
    'Hopeful': [
      { root: 'C', quality: 'major' },
      { root: 'A', quality: 'minor' },
      { root: 'F', quality: 'add9' },
      { root: 'G', quality: 'major' },
      { root: 'E', quality: 'min7' },
      { root: 'A', quality: 'min7' },
      { root: 'D', quality: 'min7' },
      { root: 'G', quality: 'sus4' }
    ],
    'Dark': [
      { root: 'D', quality: 'minor' },
      { root: 'A#', quality: 'major' },
      { root: 'F', quality: 'major' },
      { root: 'C', quality: 'major' },
      { root: 'D', quality: 'dim7' },
      { root: 'A', quality: 'dom7' }
    ]
  };

  const roots = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  
  const qualities = {
    'major': { label: 'Major', symbol: '', altSymbol: 'M', intervals: [0, 4, 7], notes: ['1', '3', '5'], mood: 'Bright, hopeful' },
    'minor': { label: 'Minor', symbol: 'm', altSymbol: 'min', intervals: [0, 3, 7], notes: ['1', '♭3', '5'], mood: 'Melancholic, introspective' },
    'dim': { label: 'Diminished', symbol: '°', altSymbol: 'dim', intervals: [0, 3, 6], notes: ['1', '♭3', '♭5'], mood: 'Tense, dramatic' },
    'aug': { label: 'Augmented', symbol: '+', altSymbol: 'aug', intervals: [0, 4, 8], notes: ['1', '3', '♯5'], mood: 'Unstable, ethereal' },
    'sus2': { label: 'Sus2', symbol: 'sus2', altSymbol: 'sus2', intervals: [0, 2, 7], notes: ['1', '2', '5'], mood: 'Floating, anticipatory' },
    'sus4': { label: 'Sus4', symbol: 'sus4', altSymbol: 'sus4', intervals: [0, 5, 7], notes: ['1', '4', '5'], mood: 'Suspended, yearning' },
    'maj7': { label: 'Major 7th', symbol: 'maj7', altSymbol: 'M7/Δ7', intervals: [0, 4, 7, 11], notes: ['1', '3', '5', '7'], mood: 'Dreamy, elegant' },
    'min7': { label: 'Minor 7th', symbol: 'm7', altSymbol: 'min7/-7', intervals: [0, 3, 7, 10], notes: ['1', '♭3', '5', '♭7'], mood: 'Jazzy, wistful' },
    'dom7': { label: 'Dominant 7th', symbol: '7', altSymbol: 'dom7', intervals: [0, 4, 7, 10], notes: ['1', '3', '5', '♭7'], mood: 'Resolving, pulling' },
    'maj9': { label: 'Major 9th', symbol: 'maj9', altSymbol: 'M9/Δ9', intervals: [0, 4, 7, 11, 14], notes: ['1', '3', '5', '7', '9'], mood: 'Lush, expansive' },
    'min9': { label: 'Minor 9th', symbol: 'm9', altSymbol: 'min9/-9', intervals: [0, 3, 7, 10, 14], notes: ['1', '♭3', '5', '♭7', '9'], mood: 'Dark, sophisticated' },
    'add9': { label: 'Add9', symbol: 'add9', altSymbol: '(add9)', intervals: [0, 4, 7, 14], notes: ['1', '3', '5', '9'], mood: 'Sparkly, colorful' },
    'minadd9': { label: 'Minor Add9', symbol: 'm(add9)', altSymbol: 'min(add9)', intervals: [0, 3, 7, 14], notes: ['1', '♭3', '5', '9'], mood: 'Emotional, rich' },
    'dim7': { label: 'Diminished 7th', symbol: '°7', altSymbol: 'dim7', intervals: [0, 3, 6, 9], notes: ['1', '♭3', '♭5', '♭♭7'], mood: 'Ominous, transitional' },
    'hdim7': { label: 'Half-Dim 7th', symbol: 'ø7', altSymbol: 'm7♭5', intervals: [0, 3, 6, 10], notes: ['1', '♭3', '♭5', '♭7'], mood: 'Mysterious, complex' },
    'maj7sharp5': { label: 'Maj7♯5', symbol: 'maj7♯5', altSymbol: 'M7+5', intervals: [0, 4, 8, 11], notes: ['1', '3', '♯5', '7'], mood: 'Ethereal, surreal' },
    'min7flat5': { label: 'Min7♭5', symbol: 'm7♭5', altSymbol: 'ø7', intervals: [0, 3, 6, 10], notes: ['1', '♭3', '♭5', '♭7'], mood: 'Tense, jazzy' },
    'maj6': { label: 'Major 6th', symbol: '6', altSymbol: 'M6', intervals: [0, 4, 7, 9], notes: ['1', '3', '5', '6'], mood: 'Vintage, warm' },
    'min6': { label: 'Minor 6th', symbol: 'm6', altSymbol: 'min6', intervals: [0, 3, 7, 9], notes: ['1', '♭3', '5', '6'], mood: 'Bittersweet, classic' },
    'sus2sus4': { label: 'Sus2Sus4', symbol: 'sus2sus4', altSymbol: 'sus', intervals: [0, 2, 5, 7], notes: ['1', '2', '4', '5'], mood: 'Clustered, ambient' },
    '7sharp9': { label: 'Dom7♯9', symbol: '7♯9', altSymbol: '7+9', intervals: [0, 4, 7, 10, 15], notes: ['1', '3', '5', '♭7', '♯9'], mood: 'Dissonant, colorful' },
    '7flat9': { label: 'Dom7♭9', symbol: '7♭9', altSymbol: '7-9', intervals: [0, 4, 7, 10, 13], notes: ['1', '3', '5', '♭7', '♭9'], mood: 'Bluesy, tense' },
    'add11': { label: 'Add11', symbol: 'add11', altSymbol: '(add11)', intervals: [0, 4, 5, 7], notes: ['1', '3', '4', '5'], mood: 'Crunchy, modern' },
    'maj13': { label: 'Major 13th', symbol: 'maj13', altSymbol: 'M13', intervals: [0, 4, 7, 11, 14, 21], notes: ['1', '3', '5', '7', '9', '13'], mood: 'Ultra lush, cinematic' },
  };

  const noteFrequencies = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88,
    'C2': 523.26, 'C#2': 554.36, 'D2': 587.32, 'D#2': 622.26,
    'E2': 659.26, 'F2': 698.46, 'F#2': 739.98, 'G2': 783.99,
    'G#2': 830.60, 'A2': 880.00, 'A#2': 932.32, 'B2': 987.76
  };

  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    
    const handleKeyPress = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
      
      if (e.key === ' ' && progression.length > 0) {
        e.preventDefault();
        if (isPlaying) {
          stopProgression();
        } else {
          playProgression();
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        addChord();
      } else if (e.key === 'Backspace' && progression.length > 0) {
        e.preventDefault();
        removeChord(progression.length - 1);
      } else if (e.key === '?') {
        e.preventDefault();
        setShowKeybinds(!showKeybinds);
      } else if (e.key >= '1' && e.key <= '9') {
        const rootIndex = parseInt(e.key) - 1;
        if (rootIndex < roots.length) {
          setSelectedRoot(roots[rootIndex]);
        }
      } else if (e.key.toLowerCase() === 'q') {
        setSelectedRoot(roots[9]); // A
      } else if (e.key.toLowerCase() === 'w') {
        setSelectedRoot(roots[10]); // A#
      } else if (e.key.toLowerCase() === 'e') {
        setSelectedRoot(roots[11]); // B
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (holdTimerRef.current) clearTimeout(holdTimerRef.current);
      if (holdIntervalRef.current) clearInterval(holdIntervalRef.current);
    };
  }, [progression, selectedRoot, selectedQuality, isPlaying, showKeybinds]);

  const getChordFrequencies = (root, quality) => {
    const rootIndex = roots.indexOf(root);
    const intervals = qualities[quality].intervals;
    
    return intervals.map(interval => {
      const semitones = interval % 12;
      const octaveShift = Math.floor(interval / 12);
      const noteIndex = (rootIndex + semitones) % 12;
      const noteName = octaveShift > 0 ? roots[noteIndex] + '2' : roots[noteIndex];
      return noteFrequencies[noteName];
    });
  };

  const playChord = (root, quality, duration = 0.5) => {
    const ctx = audioContextRef.current;
    const now = ctx.currentTime;
    const frequencies = getChordFrequencies(root, quality);
    
    frequencies.forEach(freq => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      
      gain.gain.setValueAtTime(volume * 0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + duration);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now);
      osc.stop(now + duration);
    });
  };

  const playProgression = async () => {
    if (isPlaying || progression.length === 0) return;
    
    setIsPlaying(true);
    stopPlaybackRef.current = false;
    
    const beatsPerChord = parseInt(timeSignature.split('/')[0]);
    const beatDuration = 60000 / bpm;
    const chordDuration = (beatDuration * beatsPerChord) / 1000;
    
    do {
      for (let i = 0; i < progression.length; i++) {
        if (stopPlaybackRef.current) break;
        
        const chord = progression[i];
        setCurrentChordIndex(i);
        playChord(chord.root, chord.quality, chordDuration * 0.9);
        await new Promise(resolve => setTimeout(resolve, chordDuration * 1000));
      }
    } while (loop && !stopPlaybackRef.current);
    
    setCurrentChordIndex(-1);
    setIsPlaying(false);
  };

  const stopProgression = () => {
    stopPlaybackRef.current = true;
    setIsPlaying(false);
    setCurrentChordIndex(-1);
  };

  const previewChord = (root, quality) => {
    if (holdingChord) return; // Don't preview if holding
    playChord(root, quality, 0.8);
    setClickedChord(`${root}-${quality}`);
    setTimeout(() => setClickedChord(null), 200);
  };

  const startHoldChord = (root, quality) => {
    setHoldingChord(`${root}-${quality}`);
    
    // Start initial sustained playback
    const ctx = audioContextRef.current;
    const now = ctx.currentTime;
    const frequencies = getChordFrequencies(root, quality);
    
    // Store oscillators for cleanup
    const oscillators = [];
    const gainNodes = [];
    
    frequencies.forEach(freq => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(volume * 0.15, now + 0.15); // Slower fade in
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now);
      oscillators.push(osc);
      gainNodes.push(gain);
    });
    
    // Store for cleanup
    holdTimerRef.current = { oscillators, gainNodes };
  };

  const stopHoldChord = () => {
    if (!holdingChord) return;
    setHoldingChord(null);
    
    if (holdTimerRef.current) {
      const { oscillators, gainNodes } = holdTimerRef.current;
      const ctx = audioContextRef.current;
      const now = ctx.currentTime;
      
      // Slower fade out to prevent clicks
      gainNodes.forEach(gain => {
        gain.gain.cancelScheduledValues(now);
        gain.gain.setValueAtTime(gain.gain.value, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      });
      
      // Stop oscillators after fade
      setTimeout(() => {
        oscillators.forEach(osc => {
          try { osc.stop(); } catch (e) {}
        });
      }, 250);
      
      holdTimerRef.current = null;
    }
    
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
  };

  // Get complementary chords based on music theory
  const getComplementaryChords = (root, quality) => {
    const rootIndex = roots.indexOf(root);
    const complementary = new Set();
    
    // Relative minor/major
    if (quality === 'major') {
      const relMinor = roots[(rootIndex + 9) % 12];
      complementary.add(`${relMinor}-minor`);
    } else if (quality === 'minor') {
      const relMajor = roots[(rootIndex + 3) % 12];
      complementary.add(`${relMajor}-major`);
    }
    
    // Dominant (V)
    const dominant = roots[(rootIndex + 7) % 12];
    complementary.add(`${dominant}-major`);
    complementary.add(`${dominant}-dom7`);
    
    // Subdominant (IV)
    const subdominant = roots[(rootIndex + 5) % 12];
    complementary.add(`${subdominant}-major`);
    complementary.add(`${subdominant}-maj7`);
    
    // Secondary dominant
    const secDom = roots[(rootIndex + 2) % 12];
    complementary.add(`${secDom}-dom7`);
    
    // Minor variants
    if (quality === 'minor' || quality === 'min7') {
      complementary.add(`${root}-min7`);
      complementary.add(`${root}-minor`);
    }
    
    // Extended variants of same root
    if (quality === 'major') {
      complementary.add(`${root}-maj7`);
      complementary.add(`${root}-maj9`);
    }
    
    return complementary;
  };

  const isComplementary = (root, quality) => {
    if (!holdingChord && !clickedChord) return false;
    
    const activeChord = holdingChord || clickedChord;
    if (!activeChord) return false;
    
    const [activeRoot, activeQuality] = activeChord.split('-');
    const currentChordKey = `${root}-${quality}`;
    
    // Don't highlight the same chord
    if (currentChordKey === activeChord) return false;
    
    const complementaries = getComplementaryChords(activeRoot, activeQuality);
    return complementaries.has(currentChordKey);
  };

  const addChord = () => {
    const newChord = {
      id: Date.now(),
      root: selectedRoot,
      quality: selectedQuality,
      symbol: selectedRoot + qualities[selectedQuality].symbol
    };
    setProgression([...progression, newChord]);
  };

  const addChordFromPalette = (root, quality) => {
    const newChord = {
      id: Date.now(),
      root: root,
      quality: quality,
      symbol: root + qualities[quality].symbol
    };
    setProgression([...progression, newChord]);
  };

  const removeChord = (index) => {
    setProgression(progression.filter((_, i) => i !== index));
  };

  const loadPreset = (presetName) => {
    const preset = presets[presetName];
    const newProgression = preset.map((chord, i) => ({
      id: Date.now() + i,
      root: chord.root,
      quality: chord.quality,
      symbol: chord.root + qualities[chord.quality].symbol
    }));
    setProgression(newProgression);
  };

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;
    
    const newProgression = [...progression];
    const draggedItem = newProgression[draggedIndex];
    newProgression.splice(draggedIndex, 1);
    newProgression.splice(index, 0, draggedItem);
    
    setProgression(newProgression);
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Top Bar Overlay */}
        <div className="fixed top-0 left-0 right-0 bg-gray-800/95 backdrop-blur-sm border-b border-gray-700 z-50 px-4 py-3">
          <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-4 flex-1">
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-400">Root</label>
                <select 
                  value={selectedRoot}
                  onChange={(e) => setSelectedRoot(e.target.value)}
                  className="bg-gray-700 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {roots.map(root => (
                    <option key={root} value={root}>{root}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-center gap-2 flex-1 max-w-xs">
                <label className="text-xs text-gray-400">Quality</label>
                <select 
                  value={selectedQuality}
                  onChange={(e) => setSelectedQuality(e.target.value)}
                  className="w-full bg-gray-700 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(qualities).map(([key, val]) => (
                    <option key={key} value={key}>{val.label}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={addChord}
                className="bg-blue-600 hover:bg-blue-700 rounded px-3 py-1 text-sm flex items-center gap-1 transition-colors"
              >
                <Plus size={14} />
                Add
              </button>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:block text-2xl font-bold">
                {selectedRoot}{qualities[selectedQuality].symbol}
              </div>
              
              <button
                onClick={() => setShowKeybinds(!showKeybinds)}
                className="bg-gray-700 hover:bg-gray-600 rounded p-2 transition-colors"
                title="Show keybinds"
              >
                <Keyboard size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Keybinds Overlay */}
        {showKeybinds && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowKeybinds(false)}>
            <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full border border-gray-700" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">Keyboard Shortcuts</h3>
                <button onClick={() => setShowKeybinds(false)} className="text-gray-400 hover:text-white">✕</button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-semibold text-blue-400 mb-2">Playback</h4>
                  <div className="space-y-1 text-gray-300">
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">Space</kbd> Play/Stop</div>
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">Enter</kbd> Add Chord</div>
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">Backspace</kbd> Remove Last</div>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-blue-400 mb-2">Root Notes</h4>
                  <div className="space-y-1 text-gray-300">
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">1-9</kbd> C to G#</div>
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">Q</kbd> A</div>
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">W</kbd> A#</div>
                    <div><kbd className="bg-gray-700 px-2 py-1 rounded">E</kbd> B</div>
                  </div>
                </div>
                <div className="md:col-span-2">
                  <h4 className="font-semibold text-blue-400 mb-2">Chord Palette</h4>
                  <div className="text-gray-300">
                    <div>Click: Preview chord (single play)</div>
                    <div>Click & Hold: Loop chord playback</div>
                    <div>Drag: Add to progression</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="pt-20 mb-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-2">Chord Progression Builder</h1>
          <p className="text-gray-400 text-sm">
            Press <kbd className="bg-gray-700 px-2 py-1 rounded text-xs">?</kbd> to show all keyboard shortcuts
          </p>
        </div>

        {/* Chord Builder */}
        <div className="bg-gray-800 rounded-lg p-4 md:p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Current Chord Preview</h2>

          <div className="bg-gray-700 rounded p-4">
            <div className="text-sm text-gray-400 mb-1">Selected Chord</div>
            <div className="text-3xl font-bold mb-2">
              {selectedRoot}{qualities[selectedQuality].symbol}
              <span className="text-lg text-gray-400 ml-2">({qualities[selectedQuality].altSymbol})</span>
            </div>
            <div className="text-sm text-gray-300 mb-1">
              Mood: <span className="text-blue-400">{qualities[selectedQuality].mood}</span>
            </div>
            <div className="text-xs text-gray-500">
              Notes: {qualities[selectedQuality].notes.join(' - ')} | Intervals: {qualities[selectedQuality].intervals.join(', ')}
            </div>
          </div>
        </div>

        {/* Presets */}
        <div className="bg-gray-800 rounded-lg p-4 md:p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Artcore Presets</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.keys(presets).map(presetName => (
              <button
                key={presetName}
                onClick={() => loadPreset(presetName)}
                className="bg-gray-700 hover:bg-gray-600 rounded px-4 py-3 text-sm font-medium transition-colors text-left"
              >
                {presetName}
              </button>
            ))}
          </div>
        </div>

        {/* Progression */}
        <div className="bg-gray-800 rounded-lg p-4 md:p-6 mb-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
            <h2 className="text-xl font-semibold">Your Progression</h2>
            <div className="flex flex-wrap gap-2 md:gap-3 items-center">
              <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={loop}
                  onChange={(e) => setLoop(e.target.checked)}
                  className="w-4 h-4"
                />
                Loop
              </label>
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-400">BPM</label>
                <input
                  type="number"
                  min="40"
                  max="240"
                  value={bpm}
                  onChange={(e) => setBpm(parseInt(e.target.value))}
                  className="w-16 bg-gray-700 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-400">Time</label>
                <select
                  value={timeSignature}
                  onChange={(e) => setTimeSignature(e.target.value)}
                  className="bg-gray-700 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="3/4">3/4</option>
                  <option value="4/4">4/4</option>
                  <option value="5/4">5/4</option>
                  <option value="6/8">6/8</option>
                  <option value="7/8">7/8</option>
                </select>
              </div>
              {isPlaying ? (
                <button
                  onClick={stopProgression}
                  className="bg-red-600 hover:bg-red-700 rounded px-4 py-2 flex items-center gap-2 transition-colors"
                >
                  <Square size={18} />
                  Stop
                </button>
              ) : (
                <button
                  onClick={playProgression}
                  disabled={progression.length === 0}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded px-4 py-2 flex items-center gap-2 transition-colors"
                >
                  <Play size={18} />
                  Play
                </button>
              )}
            </div>
          </div>

          {progression.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No chords yet. Add some or drag from the palette below!
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {progression.map((chord, index) => (
                <div
                  key={chord.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragEnd={handleDragEnd}
                  className={`rounded-lg px-4 md:px-6 py-3 md:py-4 flex items-center gap-2 md:gap-3 group transition-all cursor-move ${
                    currentChordIndex === index 
                      ? 'bg-blue-600 ring-2 ring-blue-400 scale-105' 
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  <GripVertical size={16} className="text-gray-500 group-hover:text-gray-300" />
                  <span className="text-xs md:text-sm text-gray-400">{index + 1}</span>
                  <span className="text-xl md:text-2xl font-bold">{chord.symbol}</span>
                  <button
                    onClick={() => removeChord(index)}
                    className="text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Volume Control */}
        <div className="bg-gray-800 rounded-lg p-4 md:p-6 mb-6">
          <div className="flex items-center gap-4">
            <Volume2 size={20} className="text-gray-400" />
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              className="flex-1"
            />
            <span className="text-sm text-gray-400 w-12 text-right">
              {Math.round(volume * 100)}%
            </span>
          </div>
        </div>

        {/* Chord Palette */}
        <div className="bg-gray-800 rounded-lg p-4 md:p-6">
          <h3 className="text-lg font-semibold mb-3">Artcore Chord Palette</h3>
          <p className="text-sm text-gray-400 mb-4">Click to preview • Click & hold to loop • Drag to add</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {Object.entries(qualities).map(([key, val]) => (
              <div
                key={key}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('chordQuality', key);
                }}
                onMouseDown={() => startHoldChord(selectedRoot, key)}
                onMouseUp={stopHoldChord}
                onMouseLeave={stopHoldChord}
                onTouchStart={() => startHoldChord(selectedRoot, key)}
                onTouchEnd={stopHoldChord}
                onClick={() => previewChord(selectedRoot, key)}
                onDragEnd={(e) => {
                  if (e.dataTransfer.dropEffect === 'none') {
                    addChordFromPalette(selectedRoot, key);
                  }
                }}
                className={`bg-gray-700 hover:bg-gray-600 rounded p-3 cursor-grab active:cursor-grabbing select-none transition-all duration-200 ease-in-out ${
                  clickedChord === `${selectedRoot}-${key}` ? 'ring-2 ring-blue-400 scale-95' : ''
                } ${
                  holdingChord === `${selectedRoot}-${key}` ? 'ring-4 ring-green-400 scale-105 bg-gray-600' : ''
                }`}
              >
                <div className="font-semibold text-blue-400 mb-1">
                  {selectedRoot}{val.symbol}
                  <span className="text-xs text-gray-400 ml-2">({val.altSymbol})</span>
                </div>
                <div className="text-gray-300 text-xs mb-1">{val.label}</div>
                <div className="text-gray-500 text-xs mb-1">{val.mood}</div>
                <div className="text-gray-600 text-xs font-mono">
                  {val.notes.join(' ')}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-gray-700">
            <h4 className="font-semibold mb-3 text-blue-400">Click a preset above to load instantly!</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-300">
              <div><span className="text-gray-500">Dramatic:</span> Am → F → Cmaj7 → G → Em → Dm7 → Esus4 → E</div>
              <div><span className="text-gray-500">Emotional:</span> Cmaj9 → Am9 → Fmaj7 → Gsus4 → G7</div>
              <div><span className="text-gray-500">Epic:</span> Dm → B♭maj7 → C → Am → Gm7 → A7</div>
              <div><span className="text-gray-500">Ethereal:</span> Cmaj7 → Em9 → Am7 → Fmaj9 → Gsus4</div>
              <div><span className="text-gray-500">Tense:</span> C°7 → Dm7 → G7♯9 → Cmaj7</div>
              <div><span className="text-gray-500">Melancholic:</span> Am → Fmaj7 → C → Gm → Dm7 → E7</div>
              <div><span className="text-gray-500">Hopeful:</span> C → Am → Fadd9 → G → Em7 → Am7 → Dm7 → Gsus4</div>
              <div><span className="text-gray-500">Dark:</span> Dm → B♭ → F → C → D°7 → A7</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChordProgressionApp;