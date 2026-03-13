# JummBox Analyzer Roadmap

Feature implementation plan sorted by quality-of-life impact.

## Priority 1: Timeline & Arrangement (High QoL)

### 1. Timeline reconstruction command
- [x] Add `timeline` subcommand
- [x] Reconstruct song arrangement from `sequence + patterns + notes`
- [x] Output: sequence slot, channel, pattern, tick range, note summary

### 2. Bar-by-bar arrangement view
- [x] Add `arrangement` subcommand
- [x] Compact grid showing pattern per channel per bar/slot
- [x] Reveal structure, repetition, intros, drops

### 3. Channel role guessing
- [x] Detect: melody, chords, bass, drums/noise, modulation, utility
- [x] Heuristics: instrument type, pitch range, note density, polyphony

### 4. Chord estimation
- [ ] Estimate chord names from simultaneous pitched notes
- [ ] Options: `--window bar`, `--window half-bar`, `--window beat`

### 5. Better summary mode
- [ ] Top 3 issues
- [ ] Likely channel roles
- [ ] Total used vs unused content
- [ ] Approximate length in bars
- [ ] Busiest channels, most repeated patterns

## Priority 2: Diagnostics & Cleanup

### 6. Sequence reference diagnostics
- [ ] Show exact channel and slot for invalid refs
- [ ] Suggest nearest valid pattern index
- [ ] Distinguish null/empty/rest-like from bad refs

### 7. Cleanup/fix mode
- [ ] `fix --dry-run` / `fix --apply`
- [ ] Remove unused empty patterns
- [ ] Report stale non-empty patterns
- [ ] Compact pattern banks
- [ ] Remove invalid sequence refs
- [ ] Deduplicate exact copies

### 8. Activity heatmap
- [ ] Text-mode visualization of channel activity across time
- [ ] Highlight drops, transitions, sparse sections

## Priority 3: Analysis Improvements

### 9. Pitch-class and key analysis
- [ ] Pitch-class analysis (C, C#, D, etc.)
- [ ] Key center estimation (global and by section)

### 10. Section detection
- [ ] Auto-label: intro, verse, chorus, bridge, outro
- [ ] Cluster repeated arrangement blocks

### 11. Bar length / duration reporting
- [x] Total bars/slots
- [x] Estimated real time duration
- [x] Tempo if available

### 12. Channel filtering improvements
- [ ] Multiple channels: `--channel 0,1,2`
- [ ] Ranges: `--channels 4-8`
- [ ] Include/exclude: `--exclude-mod`
- [ ] Only audible/mod channels

### 13. Bar/slot range filtering
- [ ] `--from-slot`, `--to-slot`
- [ ] `--from-bar`, `--to-bar`

## Priority 4: Export & Integration

### 14. CSV export
- [ ] Timeline, note events, pattern usage, lint findings

### 15. Diff mode
- [ ] Compare two JSON files
- [ ] Show channels/patterns/notes changed

### 16. Markdown report output
- [ ] Generate `.md` report for sharing

## Priority 5: UI & Polish

### 17. Colorized terminal output
- [ ] Errors, warnings, section headers, health level

### 18. Compact table mode
- [ ] Narrower/tabular output

### 19. Severity levels for lint
- [ ] info, warning, error levels

### 20. Machine-friendly exit codes
- [ ] Invalid file, health threshold, broken refs

---

## Implementation Log

### 2026-03-13
- Added `info` subcommand (tempo, bars, duration)
- Added `timeline` subcommand (sequence reconstruction)
- Added `arrangement` subcommand (bar-by-bar grid view)
- Added `roles` subcommand (channel role detection)

### 2026-03-12
- Added `strings` subcommand for raw unique string extraction
