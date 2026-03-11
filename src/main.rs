// main.rs
//
// Purpose: Entry point for JummBox TUI analyzer

mod app;
mod data;
mod ui;

use color_eyre::Result;
use ratatui::DefaultTerminal;

fn main() -> Result<()> {
    color_eyre::install()?;
    let terminal = ratatui::init();
    let app_result = run(terminal);
    ratatui::restore();
    app_result
}

fn run(mut terminal: DefaultTerminal) -> Result<()> {
    let mut app = app::App::new();
    app.run(&mut terminal)
}
