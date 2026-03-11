// app.rs
//
// Purpose: Application state and event handling

use crate::data::JummBoxFile;
use crate::ui::render_ui;
use color_eyre::Result;
use ratatui::{
    crossterm::event::{self, Event, KeyCode, KeyEventKind},
    DefaultTerminal, Frame,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CurrentScreen {
    Main,
    Editing,
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
        match key_code {
            KeyCode::Char('e') => {
                self.current_screen = CurrentScreen::Editing;
                self.currently_editing = Some(EditingField::FilePath);
            }
            KeyCode::Char('f') => {
                self.current_screen = CurrentScreen::Editing;
                self.currently_editing = Some(EditingField::FilterQuery);
            }
            KeyCode::Char('l') => self.load_file(),
            KeyCode::Char('q') => self.current_screen = CurrentScreen::Exiting,
            KeyCode::Up => self.scroll_up(),
            KeyCode::Down => self.scroll_down(),
            _ => {}
        }
    }

    fn handle_editing_input(&mut self, key_code: KeyCode) {
        match key_code {
            KeyCode::Enter => self.save_editing(),
            KeyCode::Backspace => self.delete_char(),
            KeyCode::Esc => {
                self.current_screen = CurrentScreen::Main;
                self.currently_editing = None;
            }
            KeyCode::Tab => self.toggle_editing(),
            KeyCode::Char(c) => self.enter_char(c),
            _ => {}
        }
    }

    fn handle_exiting_input(&mut self, key_code: KeyCode) -> bool {
        match key_code {
            KeyCode::Char('y') => true,
            KeyCode::Char('n') | KeyCode::Char('q') => {
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
        match JummBoxFile::from_file(&self.file_path) {
            Ok(data) => {
                self.data = Some(data);
                self.error_message = None;
            }
            Err(e) => {
                self.error_message = Some(format!("Failed to load: {}", e));
            }
        }
    }

    fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }

    fn scroll_down(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_add(1);
    }

    fn draw(&self, frame: &mut Frame) {
        render_ui(frame, self);
    }
}
