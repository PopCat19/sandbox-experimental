// app.rs
//
// Purpose: Application state and event handling

use crate::data::JummBoxFile;
use crate::ui::render_ui;
use color_eyre::Result;
use log::{debug, info, warn};
use ratatui::{
    crossterm::event::{self, Event, KeyCode, KeyEventKind},
    DefaultTerminal, Frame,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CurrentScreen {
    Main,
    Editing,
    FilePicker,
    Exiting,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EditingField {
    FilePath,
    FilterQuery,
}

pub struct App {
    pub current_screen: CurrentScreen,
    pub currently_editing: Option<EditingField>,
    pub file_path: String,
    pub filter_query: String,
    pub cursor_position: usize,
    pub data: Option<JummBoxFile>,
    pub error_message: Option<String>,
    pub scroll_offset: usize,
}

impl App {
    pub fn new() -> Self {
        Self {
            current_screen: CurrentScreen::Main,
            currently_editing: None,
            file_path: String::from("./slarmoosbox.json"),
            filter_query: String::new(),
            cursor_position: 0,
            data: None,
            error_message: None,
            scroll_offset: 0,
        }
    }

    pub fn run(&mut self, terminal: &mut DefaultTerminal) -> Result<()> {
        loop {
            terminal.draw(|frame| self.draw(frame))?;

            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Release {
                    continue;
                }

                match self.current_screen {
                    CurrentScreen::Main => self.handle_main_input(key.code),
                    CurrentScreen::Editing => self.handle_editing_input(key.code),
                    CurrentScreen::FilePicker => self.handle_file_picker_input(key.code),
                    CurrentScreen::Exiting => {
                        if self.handle_exiting_input(key.code) {
                            return Ok(());
                        }
                    }
                }
            }
        }
    }

    fn handle_main_input(&mut self, key_code: KeyCode) {
        debug!("main input: {:?}", key_code);
        match key_code {
            KeyCode::Char('e') => {
                info!("opening editor for path entry");
                self.open_editor_for_path();
            }
            KeyCode::Char('f') => {
                info!("entering edit mode for filter query");
                self.current_screen = CurrentScreen::Editing;
                self.currently_editing = Some(EditingField::FilterQuery);
            }
            KeyCode::Char('l') => self.load_file(),
            KeyCode::Char('q') => {
                info!("requesting exit");
                self.current_screen = CurrentScreen::Exiting;
            }
            KeyCode::Up => self.scroll_up(),
            KeyCode::Down => self.scroll_down(),
            _ => {}
        }
    }

    fn handle_editing_input(&mut self, key_code: KeyCode) {
        debug!("editing input: {:?}", key_code);
        match key_code {
            KeyCode::Enter => self.save_editing(),
            KeyCode::Backspace => self.delete_char(),
            KeyCode::Esc => {
                info!("canceling edit mode");
                self.current_screen = CurrentScreen::Main;
                self.currently_editing = None;
            }
            KeyCode::Tab => self.toggle_editing(),
            // Vim keys: h=left, j=down, k=up, l=right
            KeyCode::Char('h') => self.move_cursor_left(),
            KeyCode::Char('j') => self.move_cursor_down(),
            KeyCode::Char('k') => self.move_cursor_up(),
            KeyCode::Char('l') => self.move_cursor_right(),
            // Arrow keys also supported
            KeyCode::Left => self.move_cursor_left(),
            KeyCode::Right => self.move_cursor_right(),
            KeyCode::Char(c) => self.enter_char(c),
            _ => {}
        }
    }

    fn handle_exiting_input(&mut self, key_code: KeyCode) -> bool {
        debug!("exit input: {:?}", key_code);
        match key_code {
            KeyCode::Char('y') => {
                info!("user confirmed exit");
                true
            }
            KeyCode::Char('n') | KeyCode::Char('q') => {
                info!("user canceled exit");
                self.current_screen = CurrentScreen::Main;
                false
            }
            _ => false,
        }
    }

    fn toggle_editing(&mut self) {
        if let Some(edit_mode) = &self.currently_editing {
            match edit_mode {
                EditingField::FilePath => {
                    self.currently_editing = Some(EditingField::FilterQuery)
                }
                EditingField::FilterQuery => {
                    self.currently_editing = Some(EditingField::FilePath)
                }
            };
        } else {
            self.currently_editing = Some(EditingField::FilePath);
        }
    }

    fn save_editing(&mut self) {
        if let Some(edit_mode) = &self.currently_editing {
            match edit_mode {
                EditingField::FilePath => {
                    self.currently_editing = Some(EditingField::FilterQuery);
                }
                EditingField::FilterQuery => {
                    self.current_screen = CurrentScreen::Main;
                    self.currently_editing = None;
                }
            }
        }
    }

    fn enter_char(&mut self, new_char: char) {
        if let Some(editing) = &self.currently_editing {
            match editing {
                EditingField::FilePath => self.file_path.push(new_char),
                EditingField::FilterQuery => self.filter_query.push(new_char),
            }
        }
    }

    fn delete_char(&mut self) {
        if let Some(editing) = &self.currently_editing {
            match editing {
                EditingField::FilePath => {
                    self.file_path.pop();
                }
                EditingField::FilterQuery => {
                    self.filter_query.pop();
                }
            }
        }
    }

    fn load_file(&mut self) {
        info!("loading file: {}", self.file_path);
        // Check if file exists, if not open file picker
        if !std::path::Path::new(&self.file_path).exists() {
            warn!("file does not exist, opening file picker");
            self.current_screen = CurrentScreen::FilePicker;
            self.cursor_position = self.file_path.len();
            return;
        }
        match JummBoxFile::from_file(&self.file_path) {
            Ok(data) => {
                info!(
                    "file loaded: {} channels, {} notes",
                    data.channel_count(),
                    data.total_notes()
                );
                self.data = Some(data);
                self.error_message = None;
            }
            Err(e) => {
                warn!("failed to load file: {}", e);
                self.error_message = Some(format!("Failed to load: {}", e));
            }
        }
    }

    fn handle_file_picker_input(&mut self, key_code: KeyCode) {
        debug!("file picker input: {:?}", key_code);
        match key_code {
            KeyCode::Enter => {
                info!("file picker: attempting to load file");
                self.current_screen = CurrentScreen::Main;
                self.load_file();
            }
            KeyCode::Esc => {
                info!("file picker: canceling");
                self.current_screen = CurrentScreen::Main;
            }
            KeyCode::Backspace => {
                self.file_path.pop();
                self.cursor_position = self.cursor_position.saturating_sub(1);
            }
            // Vim keys
            KeyCode::Char('h') => self.move_cursor_left(),
            KeyCode::Char('j') => self.move_cursor_down(),
            KeyCode::Char('k') => self.move_cursor_up(),
            KeyCode::Char('l') => self.move_cursor_right(),
            KeyCode::Char('/') => {
                self.current_screen = CurrentScreen::Editing;
                self.currently_editing = Some(EditingField::FilePath);
            }
            // Arrow keys
            KeyCode::Left => self.move_cursor_left(),
            KeyCode::Right => self.move_cursor_right(),
            KeyCode::Char(c) => {
                self.file_path.push(c);
                self.cursor_position += 1;
            }
            _ => {}
        }
    }

    fn move_cursor_left(&mut self) {
        self.cursor_position = self.cursor_position.saturating_sub(1);
    }

    fn move_cursor_right(&mut self) {
        let max_pos = self.file_path.len();
        if self.cursor_position < max_pos {
            self.cursor_position += 1;
        }
    }

    fn move_cursor_up(&mut self) {
        self.scroll_up();
    }

    fn move_cursor_down(&mut self) {
        self.scroll_down();
    }

    fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }

    fn scroll_down(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_add(1);
    }

    fn open_editor_for_path(&mut self) {
        // Create a temp file with the current path
        let temp_path = std::env::temp_dir().join("slarmoosbox_path.txt");
        if let Err(e) = std::fs::write(&temp_path, &self.file_path) {
            warn!("failed to write temp file: {}", e);
            return;
        }

        // Get editor from env or use default
        let editor = std::env::var("EDITOR").unwrap_or_else(|_| "vi".to_string());
        info!("opening editor: {} {}", editor, temp_path.display());

        // Open editor
        let result = std::process::Command::new(&editor)
            .arg(&temp_path)
            .status();

        match result {
            Ok(status) if status.success() => {
                // Read back the path
                match std::fs::read_to_string(&temp_path) {
                    Ok(content) => {
                        let new_path = content.trim().to_string();
                        if !new_path.is_empty() {
                            self.file_path = new_path;
                            info!("path updated from editor");
                        }
                    }
                    Err(e) => {
                        warn!("failed to read temp file: {}", e);
                    }
                }
            }
            Ok(status) => {
                warn!("editor exited with status: {:?}", status);
            }
            Err(e) => {
                warn!("failed to open editor: {}", e);
            }
        }

        // Clean up temp file
        let _ = std::fs::remove_file(&temp_path);
    }

    fn draw(&self, frame: &mut Frame) {
        render_ui(frame, self);
    }
}
