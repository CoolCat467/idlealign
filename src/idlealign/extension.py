"""Idle Align - Emacs Align by Regular Expression as an IDLE Extension."""

# Programmed by CoolCat467

from __future__ import annotations

# Copyright (C) 2022-2024  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "extension"
__author__ = "CoolCat467"
__license__ = "GNU General Public License Version 3"

from tkinter import BooleanVar, Event, Frame, Tk, Variable
from tkinter.ttk import Checkbutton, Radiobutton
from typing import TYPE_CHECKING, Any, ClassVar, cast

from idlelib import searchengine
from idlelib.searchbase import SearchDialogBase

from idlealign import utils

if TYPE_CHECKING:
    from re import Pattern


class AlignDialog(SearchDialogBase):  # type: ignore[misc]
    """Dialog for aligning by a pattern in text."""

    __slots__ = (
        "insert_tags",
        "align_side_var",
        "extension",
        "prev_search_params",
        "space_wrap_var",
        "search_params",
        "global_search_params",
        "selection",
    )
    title = "Align Dialog"
    icon = "Align"
    needwrapbutton = False

    def __init__(
        self,
        root: Tk,
        engine: searchengine.SearchEngine,
        extension: idlealign,
    ) -> None:
        """Create search dialog for aligning text.

        Uses SearchDialogBase as the basis for the GUI and a
        searchengine instance to prepare the search.

        Attributes
        ----------
            space_wrap_var: BooleanVar of if the align text should be wrapped with spaces
            insert_tags: Optional string of tags for text insert
            extension: Extension class
            prev_search_params: Dictionary of search parameters before opening window

        """
        super().__init__(root, engine)
        self.insert_tags: str | list[str] | tuple[str, ...] = ()

        self.space_wrap_var = BooleanVar(
            root,
            True,
        )  # Space wrap alignment pattern?
        self.align_side_var = BooleanVar(root, False)  # Alignment side var

        self.extension = extension

        self.global_search_params: dict[str, str | bool]
        self.search_params: dict[str, str | bool] = {
            "wrap": False,
            "back": False,
        }

        self.selection = utils.get_selected_text_indexes(self.extension.text)

    def load_prefs(self) -> None:
        """Load search engine preferences."""
        self.global_search_params = utils.get_search_engine_params(self.engine)
        utils.set_search_engine_params(self.engine, self.search_params)

    def store_prefs(self) -> None:
        """Restore global search engine preferences."""
        self.search_params = utils.get_search_engine_params(self.engine)
        utils.set_search_engine_params(self.engine, self.global_search_params)

    def open(
        self,
        searchphrase: str | None = None,
        insert_tags: str | list[str] | tuple[str, ...] = (),
    ) -> None:
        """Make dialog visible on top of others and ready to use.

        Also, highlight the currently selected text.

        Arguments:
        ---------
            searchphrase: Search phrase to look for or existing phrase.
            insert_tags: Tags to use when inserting text.

        """
        self.load_prefs()

        text = self.extension.text

        super().open(text, searchphrase)

        self.insert_tags = insert_tags

        self.selection = utils.get_selected_text_indexes(text)
        utils.show_hit(text, *self.selection)

    def close(self, event: Event[Any] | None = None) -> None:
        """Close the dialog and remove hit tags."""
        super().close(event)

        # Restore global search engine preferences
        self.store_prefs()

        utils.hide_hit(self.extension.text)
        self.insert_tags = ()

    def create_option_buttons(
        self,
    ) -> tuple[Frame, list[tuple[Variable, str]]]:
        """Create option buttons."""
        frame: Frame
        base_options: list[tuple[Variable, str]]
        frame, base_options = super().create_option_buttons()
        options = [(self.space_wrap_var, "Space wrap")]
        for var, label in options:
            btn = Checkbutton(frame, variable=var, text=label)
            btn.pack(side="left", fill="both")
            base_options.append((var, label))
        return frame, base_options

    def create_other_buttons(self) -> tuple[Frame, list[tuple[bool, str]]]:
        """Override so Search Direction is instead Alignment Side."""
        frame = self.make_frame("Alignment Side")[0]
        var = self.align_side_var
        others = [(False, "Left"), (True, "Right")]
        for val, label in others:
            btn = Radiobutton(frame, variable=var, value=val, text=label)
            btn.pack(side="left", fill="both")
        return frame, others

    def create_command_buttons(self) -> None:
        """Create command buttons."""
        super().create_command_buttons()
        self.make_button("Align", self.default_command, isdef=True)

    def default_command(self, _event: Event[Any] | None = None) -> bool:
        """Handle align again as the default command."""
        if not self.engine.getpat():
            self.open()
            return False

        pattern = self.engine.getprog()
        if not pattern:
            return False

        space_wrap: bool = self.space_wrap_var.get()
        align_side: bool = self.align_side_var.get()

        close = self.extension.align_selection(
            self.selection,
            pattern,
            space_wrap,
            align_side,
            self.insert_tags,
        )

        if close:
            # Close window
            self.close()
        else:
            # Ring bell because something went wrong
            self.bell()
        return close


# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.


class idlealign(utils.BaseExtension):  # noqa: N801
    """Add comments from mypy to an open program."""

    __slots__ = ()

    # Extend the file and format menus.
    menudefs: ClassVar = [
        ("format", [("Align Selection", "<<align-selection>>")]),
    ]

    # Default key binds for configuration file
    bind_defaults: ClassVar = {
        "align-selection": "<Alt-Key-a>",
    }

    @property
    def window(self) -> AlignDialog:
        """Window for current text widget."""
        return self.create_window()

    def create_window(self) -> AlignDialog:
        """Create align dialog window."""
        root: Tk
        root = self.text._root()  # type: ignore[attr-defined]

        engine: searchengine.SearchEngine = searchengine.get(root)

        if not hasattr(engine, "_aligndialog"):
            engine._aligndialog = AlignDialog(root, engine, self)
        return cast(AlignDialog, engine._aligndialog)

    def align_selection(
        self,
        selection: tuple[str, str],
        pattern: Pattern[str],
        space_wrap: bool = True,
        align_side: bool = False,
        tags: str | list[str] | tuple[str, ...] = (),
    ) -> bool:
        """Align selection by pattern. Side False == left.

        Return True if should close window.
        """
        # Get start and end from selection, both are strings of {line}.{col}
        select_start, select_end = selection

        # Get full first line till one past end line from selection
        select_start = utils.get_whole_line(select_start)
        grab_end = utils.get_whole_line(select_end, 1)

        # Get the characters from full line selection
        chars: str = self.text.get(select_start, grab_end)

        # Split lines
        lines = chars.splitlines()
        # Keeping track of lines to modify
        line_data: dict[int, tuple[str, str]] = {}

        # Finding min width excluding spaces of all lines till start of align pattern
        sec_start = 0
        for idx, line in enumerate(lines):
            # Regular expression match
            match = pattern.search(line)

            if match is None:  # If align pattern not in line, skip line
                continue

            # Get the where alignment pattern starts and ends at
            start, end = match.span()

            prefix = line[:start]
            align = line[start:end]
            suffix = line[end:]

            # If space wrap is set, wrap alignment text with spaces
            if space_wrap:
                align = f" {align} "

            if not align_side:  # If align to left side
                # Strip trailing spaces before align but keep indent
                prefix = prefix.rstrip()
                suffix = align + suffix.strip()  # Strip extra spaces
            else:  # If align to right side
                prefix += align.lstrip()
                suffix = suffix.lstrip()

            line_data[idx] = (prefix, suffix)  # Remember after we get max

            sec_start = max(sec_start, len(prefix))  # Update max

        if not line_data:
            # There are no lines with selected pattern so stop
            return False

        changed = False
        # For each line selected that had align pattern, add or remove
        # spaces from start up to pattern so each pattern starts in the same column
        for key, value in line_data.items():
            prefix, suffix = value

            new = prefix.ljust(sec_start) + suffix

            if lines[key] != new:
                changed = True
                lines[key] = new

        if not changed:
            # There was no change so stop
            return False

        # Add extra blank line because of how insert works
        lines.append("")
        # Re-get characters to set
        chars = "\n".join(lines)

        # This is all one operation
        with utils.undo_block(self.undo):
            # Replace old text with new aligned text
            self.text.delete(select_start, grab_end)
            self.text.insert(select_start, chars, tags)

        ## # Select modified area
        ## utils.show_hit(self.text, select_start, grab_end)
        return True

    def align_selection_event(self, _event: Event[Any] | None) -> str:
        """Align selected text."""
        self.reload()

        self.window.open()
        return "break"
