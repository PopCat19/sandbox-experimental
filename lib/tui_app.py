# tui_app.py
#
# Purpose: Implements a dual-pane Textual application for JummBox analysis
#
# This module:
# - Builds the Textual layout
# - Handles file selection and key bindings (including vim-style)
# - Updates the analyzer pane on demand

from __future__ import annotations

import os
from pathlib import Path

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DirectoryTree
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Static

from lib.tui_render import build_status_line
from lib.tui_render import render_selected_path
from lib.tui_state import ViewState


class SlarmoosboxTuiApp(App[None]):
    # SlarmoosboxTuiApp
    #
    # Purpose: Runs a ranger-like file browser and analysis viewer
    #
    # This module:
    # - Displays the filesystem in the left pane
    # - Displays analysis output in the right pane
    # - Synchronizes selection state with rendered output

    CSS_PATH = "../slarmoosbox.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("enter", "open_selected", "Analyze"),
        Binding("m", "cycle_mode", "Mode"),
        Binding("M", "cycle_mode_reverse", "Mode rev"),
        Binding("s", "cycle_section", "Section"),
        Binding("S", "cycle_section_reverse", "Section rev"),
        Binding("r", "reload_view", "Reload"),
        Binding("]", "channel_up", "Channel +"),
        Binding("[", "channel_down", "Channel -"),
        Binding("}", "channel_up", "Channel +"),
        Binding("{", "channel_down", "Channel -"),
        Binding("c", "clear_channel", "Clear channel"),
        Binding("home", "go_root", "Root"),
        Binding("~", "go_home", "Home"),
        Binding("/", "go_input", "Input path"),
        # Vim-style navigation
        Binding("j", "tree_down", "Down"),
        Binding("k", "tree_up", "Up"),
        Binding("h", "tree_parent", "Parent"),
        Binding("l", "tree_select", "Open"),
    ]

    selected_path: reactive[Path | None] = reactive(None)

    def __init__(self, initial_path: Path) -> None:
        super().__init__()
        browse_root = initial_path if initial_path.is_dir() else initial_path.parent

        self.state = ViewState(
            current_path=browse_root,
            selected_file=initial_path if initial_path.is_file() else None,
        )

        if self.state.selected_file is not None:
            self.selected_path = self.state.selected_file

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="app-shell"):
            yield DirectoryTree(str(self.state.current_path), id="file-tree")

            with Vertical(id="right-pane"):
                yield Static("", id="status-bar")
                yield Static("", id="report-view")

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Slarmoosbox TUI"
        self.sub_title = "Dual-pane JummBox JSON analyzer"
        self._refresh_view()

        tree = self.query_one("#file-tree", DirectoryTree)
        tree.focus()

        if self.state.selected_file is not None:
            self._expand_to_path(self.state.selected_file)

    def _refresh_view(self) -> None:
        self.state.selected_file = self.selected_path

        status_bar = self.query_one("#status-bar", Static)
        report_view = self.query_one("#report-view", Static)

        status_bar.update(build_status_line(self.state))
        report_view.update(render_selected_path(self.selected_path, self.state))

    def _expand_to_path(self, path: Path) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        try:
            tree.path = str(path.parent if path.is_file() else path)
        except Exception:
            return

    def on_directory_tree_file_selected(
        self,
        event: DirectoryTree.FileSelected,
    ) -> None:
        self.selected_path = Path(event.path)
        self._refresh_view()

    def on_directory_tree_directory_selected(
        self,
        event: DirectoryTree.DirectorySelected,
    ) -> None:
        self.selected_path = Path(event.path)
        self._refresh_view()

    def action_open_selected(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        node = tree.cursor_node

        if node is None or node.data is None:
            return

        path = Path(str(node.data.path))
        self.selected_path = path
        self._refresh_view()

    def action_tree_down(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.action_cursor_down()

    def action_tree_up(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.action_cursor_up()

    def action_tree_parent(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        node = tree.cursor_node
        if node is not None and node.parent is not None:
            parent_path = node.parent.data.path
            try:
                tree.path = str(parent_path)
            except Exception:
                return

    def action_tree_select(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        node = tree.cursor_node

        if node is None or node.data is None:
            return

        path = Path(str(node.data.path))

        if path.is_dir():
            # Enter directory
            try:
                tree.path = str(path)
            except Exception:
                return
        else:
            # Select file
            self.selected_path = path
            self._refresh_view()

    def action_cycle_mode(self) -> None:
        self.state.cycle_mode()
        self._refresh_view()

    def action_cycle_mode_reverse(self) -> None:
        self.state.cycle_mode_reverse()
        self._refresh_view()

    def action_cycle_section(self) -> None:
        self.state.cycle_section()
        self._refresh_view()

    def action_cycle_section_reverse(self) -> None:
        self.state.cycle_section_reverse()
        self._refresh_view()

    def action_reload_view(self) -> None:
        self._refresh_view()

    def action_channel_up(self) -> None:
        self.state.increment_channel_filter()
        self._refresh_view()

    def action_channel_down(self) -> None:
        self.state.decrement_channel_filter()
        self._refresh_view()

    def action_clear_channel(self) -> None:
        self.state.clear_channel_filter()
        self._refresh_view()

    def action_go_root(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.path = str(self.state.current_path)
        tree.reload()
        tree.focus()

    def action_go_home(self) -> None:
        home = Path(os.path.expanduser("~"))
        self.state.current_path = home
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.path = str(home)
        tree.reload()
        tree.focus()

    def action_go_input(self) -> None:
        def on_submit(path: str) -> None:
            p = Path(path).expanduser()
            if p.exists():
                if p.is_file():
                    self.state.current_path = p.parent
                    tree = self.query_one("#file-tree", DirectoryTree)
                    tree.path = str(p.parent)
                    self.selected_path = p
                else:
                    self.state.current_path = p
                    tree = self.query_one("#file-tree", DirectoryTree)
                    tree.path = str(p)
                self._refresh_view()
            self.app.pop_screen()

        from textual.binding import Binding
        from textual.widgets import Input
        from textual.widgets import Label
        from textual.screen import ModalScreen

        class PathInput(ModalScreen[None]):
            BINDINGS = [Binding("escape", "cancel", "Cancel")]

            def compose(self):
                yield Label("Enter path:")
                yield Input(placeholder="/home/user/...")

            def on_mount(self) -> None:
                self.query_one(Input).focus()

            def on_input_submit(self, event: Input.Submit) -> None:
                on_submit(event.value)

            def action_cancel(self) -> None:
                self.app.pop_screen()

        self.push_screen(PathInput())
