// ui.rs
//
// Purpose: UI rendering for JummBox analyzer

use crate::app::{App, CurrentScreen, EditingField};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

pub fn render_ui(frame: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(10),
            Constraint::Length(3),
        ])
        .split(frame.area());

    match app.current_screen {
        CurrentScreen::Main => {
            render_header(frame, app, chunks[0]);
            render_main_content(frame, app, chunks[1]);
        }
        CurrentScreen::Editing => {
            render_editing_header(frame, app, chunks[0]);
            render_editing_content(frame, app, chunks[1]);
        }
        CurrentScreen::FilePicker => {
            render_file_picker_header(frame, chunks[0]);
            render_file_picker_content(frame, app, chunks[1]);
        }
        CurrentScreen::Exiting => {
            render_header(frame, app, chunks[0]);
            render_exit_dialog(frame, chunks[1]);
        }
    }

    render_footer(frame, app, chunks[2]);
}

fn render_header(frame: &mut Frame, _app: &App, area: Rect) {
    let title = Line::from("JummBox Analyzer").centered();
    let block = Block::default()
        .borders(Borders::ALL)
        .title(title)
        .title_style(Style::default().fg(Color::Cyan).bold());
    frame.render_widget(block, area);
}

fn render_editing_header(frame: &mut Frame, _app: &App, area: Rect) {
    let title = Line::from("Edit Mode").centered();
    let block = Block::default()
        .borders(Borders::ALL)
        .title(title)
        .title_style(Style::default().fg(Color::Yellow).bold());
    frame.render_widget(block, area);
}

fn render_file_picker_header(frame: &mut Frame, area: Rect) {
    let title = Line::from("File Picker").centered();
    let block = Block::default()
        .borders(Borders::ALL)
        .title(title)
        .title_style(Style::default().fg(Color::Magenta).bold());
    frame.render_widget(block, area);
}

fn render_main_content(frame: &mut Frame, app: &App, area: Rect) {
    if let Some(ref error) = app.error_message {
        render_error(frame, error, area);
        return;
    }

    if let Some(ref data) = app.data {
        render_analysis(frame, data, app.scroll_offset, area);
    } else {
        render_placeholder(frame, area);
    }
}

fn render_editing_content(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Length(3)])
        .split(area);

    let file_path_style = if matches!(app.currently_editing, Some(EditingField::FilePath)) {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default()
    };

    let filter_style = if matches!(app.currently_editing, Some(EditingField::FilterQuery)) {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default()
    };

    let file_block = Block::default()
        .borders(Borders::ALL)
        .title("File Path (Tab to switch)")
        .style(file_path_style);
    let file_para = Paragraph::new(app.file_path.as_str()).block(file_block);
    frame.render_widget(file_para, chunks[0]);

    let filter_block = Block::default()
        .borders(Borders::ALL)
        .title("Filter Query")
        .style(filter_style);
    let filter_para = Paragraph::new(app.filter_query.as_str()).block(filter_block);
    frame.render_widget(filter_para, chunks[1]);
}

fn render_file_picker_content(frame: &mut Frame, app: &App, area: Rect) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title("Enter file path")
        .style(Style::default().fg(Color::Magenta));
    let para = Paragraph::new(app.file_path.as_str()).block(block);
    frame.render_widget(para, area);
}

fn render_error(frame: &mut Frame, error: &str, area: Rect) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title("Error")
        .style(Style::default().fg(Color::Red));
    let para = Paragraph::new(error).block(block);
    frame.render_widget(para, area);
}

fn render_placeholder(frame: &mut Frame, area: Rect) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title("No Data Loaded");
    let para = Paragraph::new("Press 'l' to load file, 'e' to edit path").block(block);
    frame.render_widget(para, area);
}

fn render_analysis(frame: &mut Frame, data: &crate::data::JummBoxFile, offset: usize, area: Rect) {
    let mut items: Vec<ListItem> = Vec::new();

    items.push(ListItem::new(Line::from(Span::styled(
        "=== Structure Counts ===",
        Style::default().fg(Color::Cyan).bold(),
    ))));
    items.push(ListItem::new(format!("Channels: {}", data.channel_count())));
    items.push(ListItem::new(format!(
        "Instruments: {}",
        data.total_instruments()
    )));
    items.push(ListItem::new(format!("Patterns: {}", data.total_patterns())));
    items.push(ListItem::new(format!("Notes: {}", data.total_notes())));
    items.push(ListItem::new(format!(
        "Sequence entries: {}",
        data.total_sequence_entries()
    )));

    items.push(ListItem::new(""));
    items.push(ListItem::new(Line::from(Span::styled(
        "=== Instrument Types ===",
        Style::default().fg(Color::Cyan).bold(),
    ))));

    let mut type_counts: Vec<_> = data.instrument_type_counts().into_iter().collect();
    type_counts.sort_by(|a, b| b.1.cmp(&a.1));
    for (type_name, count) in type_counts {
        items.push(ListItem::new(format!("{}: {}", type_name, count)));
    }

    items.push(ListItem::new(""));
    items.push(ListItem::new(Line::from(Span::styled(
        "=== Statistics ===",
        Style::default().fg(Color::Cyan).bold(),
    ))));
    items.push(ListItem::new(format!("Empty patterns: {}", data.empty_pattern_count())));

    items.push(ListItem::new(""));
    items.push(ListItem::new(Line::from(Span::styled(
        "=== Top Pitches ===",
        Style::default().fg(Color::Cyan).bold(),
    ))));

    let mut pitch_freq: Vec<_> = data.pitch_frequency().into_iter().collect();
    pitch_freq.sort_by(|a, b| b.1.cmp(&a.1));
    for (pitch, count) in pitch_freq.iter().take(20) {
        items.push(ListItem::new(format!("Pitch {}: {}", pitch, count)));
    }

    items.push(ListItem::new(""));
    items.push(ListItem::new(Line::from(Span::styled(
        "=== Unused Patterns ===",
        Style::default().fg(Color::Cyan).bold(),
    ))));

    for (channel, total, unused) in data.unused_patterns_by_channel() {
        items.push(ListItem::new(format!(
            "Channel {}: {} total, {} unused",
            channel, total, unused
        )));
    }

    let visible_items: Vec<ListItem> = items
        .into_iter()
        .skip(offset)
        .take(area.height as usize)
        .collect();

    let list = List::new(visible_items).block(
        Block::default()
            .borders(Borders::ALL)
            .title("Analysis Results"),
    );
    frame.render_widget(list, area);
}

fn render_exit_dialog(frame: &mut Frame, area: Rect) {
    let block = Block::default()
        .borders(Borders::ALL)
        .title("Exit?")
        .style(Style::default().fg(Color::Red));
    let para = Paragraph::new("Press 'y' to confirm, 'n' to cancel").block(block);
    frame.render_widget(para, area);
}

fn render_footer(frame: &mut Frame, app: &App, area: Rect) {
    let help_text = match app.current_screen {
        CurrentScreen::Main => "[e]dit path  [f]ilter  [l]oad  [q]uit  ↑↓ scroll",
        CurrentScreen::Editing => "[Enter] save  [Tab] switch field  [Esc] cancel  vim: h/j/k/l",
        CurrentScreen::FilePicker => "[Enter] load  [Esc] cancel  [/] edit path  vim: h/j/k/l",
        CurrentScreen::Exiting => "[y]es  [n]o",
    };

    let block = Block::default().borders(Borders::ALL);
    let para = Paragraph::new(help_text).block(block);
    frame.render_widget(para, area);
}
