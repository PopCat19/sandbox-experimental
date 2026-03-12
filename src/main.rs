// main.rs
//
// Purpose: Entry point for JummBox TUI analyzer

mod app;
mod data;
mod ui;

use color_eyre::Result;
use log::info;
use ratatui::DefaultTerminal;
use simplelog::*;

fn main() -> Result<()> {
    let log_file = std::fs::File::create("slarmoosbox-analyzer.log")?;
    WriteLogger::init(LevelFilter::Debug, Config::default(), log_file)?;
    info!("starting slarmoosbox-analyzer");
    color_eyre::install()?;
    let terminal = ratatui::init();
    info!("terminal initialized");
    let app_result = run(terminal);
    ratatui::restore();
    info!("terminal restored, exiting");
    app_result
}

fn run(mut terminal: DefaultTerminal) -> Result<()> {
    let mut app = app::App::new();
    info!("app created, entering main loop");
    app.run(&mut terminal)
}
