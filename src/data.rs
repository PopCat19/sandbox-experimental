// data.rs
//
// Purpose: JummBox JSON data structures

use serde::Deserialize;
use std::collections::HashMap;

#[derive(Debug, Deserialize, Clone)]
pub struct JummBoxFile {
    pub channels: Vec<Channel>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Channel {
    pub instruments: Vec<Instrument>,
    pub patterns: Vec<Pattern>,
    pub sequence: Vec<Option<usize>>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Instrument {
    #[serde(rename = "type")]
    pub instrument_type: String,
    pub effects: Vec<String>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Pattern {
    pub notes: Vec<Note>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Note {
    pub pitches: Vec<i32>,
    pub points: Vec<NotePoint>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct NotePoint {
    pub volume: i32,
    pub pitch_bend: i32,
    pub for_mod: bool,
}

impl JummBoxFile {
    pub fn from_file(path: &str) -> color_eyre::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let data: Self = serde_json::from_str(&content)?;
        Ok(data)
    }

    pub fn channel_count(&self) -> usize {
        self.channels.len()
    }

    pub fn total_instruments(&self) -> usize {
        self.channels.iter().map(|c| c.instruments.len()).sum()
    }

    pub fn total_patterns(&self) -> usize {
        self.channels.iter().map(|c| c.patterns.len()).sum()
    }

    pub fn total_notes(&self) -> usize {
        self.channels
            .iter()
            .flat_map(|c| c.patterns.iter())
            .map(|p| p.notes.len())
            .sum()
    }

    pub fn total_sequence_entries(&self) -> usize {
        self.channels.iter().map(|c| c.sequence.len()).sum()
    }

    pub fn instrument_type_counts(&self) -> HashMap<String, usize> {
        let mut counts = HashMap::new();
        for channel in &self.channels {
            for instrument in &channel.instruments {
                *counts.entry(instrument.instrument_type.clone()).or_insert(0) += 1;
            }
        }
        counts
    }

    pub fn empty_pattern_count(&self) -> usize {
        self.channels
            .iter()
            .flat_map(|c| c.patterns.iter())
            .filter(|p| p.notes.is_empty())
            .count()
    }

    pub fn pitch_frequency(&self) -> HashMap<i32, usize> {
        let mut counts = HashMap::new();
        for channel in &self.channels {
            for pattern in &channel.patterns {
                for note in &pattern.notes {
                    for pitch in &note.pitches {
                        *counts.entry(*pitch).or_insert(0) += 1;
                    }
                }
            }
        }
        counts
    }

    pub fn effect_counts(&self) -> HashMap<String, usize> {
        let mut counts = HashMap::new();
        for channel in &self.channels {
            for instrument in &channel.instruments {
                for effect in &instrument.effects {
                    *counts.entry(effect.clone()).or_insert(0) += 1;
                }
            }
        }
        counts
    }

    pub fn unused_patterns_by_channel(&self) -> Vec<(usize, usize, usize)> {
        self.channels
            .iter()
            .enumerate()
            .map(|(idx, channel)| {
                let total = channel.patterns.len();
                let used: Vec<usize> = channel
                    .sequence
                    .iter()
                    .filter_map(|s| *s)
                    .collect();
                let used_count = used.iter().copied().collect::<std::collections::HashSet<_>>().len();
                (idx, total, total.saturating_sub(used_count))
            })
            .collect()
    }
}
