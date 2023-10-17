"""Idle Align - Emacs Align by Regular Expression as an IDLE Extension."""

# Programmed by CoolCat467

from __future__ import annotations

__title__ = "idlealign"
__author__ = "CoolCat467"
__license__ = "GPLv3"
__version__ = "0.1.1"
__ver_major__ = 0
__ver_minor__ = 1
__ver_patch__ = 1

import sys
from re import Pattern
from tkinter import BooleanVar, Event, Frame, TclError, Text, Tk, Variable
from tkinter.ttk import Checkbutton, Radiobutton
from typing import Any, ClassVar, cast

from idlelib import searchengine
from idlelib.config import idleConf
from idlelib.pyshell import PyShellEditorWindow
from idlelib.searchbase import SearchDialogBase


def get_required_config(
    values: dict[str, str],
    bind_defaults: dict[str, str],
) -> str:
    """Get required configuration file data."""
    config = ""
    # Get configuration defaults
    settings = "\n".join(
        f"{key} = {default}" for key, default in values.items()
    )
    if settings:
        config += f"\n[{__title__}]\n{settings}"
        if bind_defaults:
            config += "\n"
    # Get key bindings data
    settings = "\n".join(
        f"{event} = {key}" for event, key in bind_defaults.items()
    )
    if settings:
        config += f"\n[{__title__}_cfgBindings]\n{settings}"
    return config


def check_installed() -> bool:
    """Make sure extension installed."""
    # Get list of system extensions
    extensions = set(idleConf.defaultCfg["extensions"])

    # Do we have the user extend extension?
    has_user = "idleuserextend" in idleConf.GetExtensions(active_only=True)

    # If we don't, things get messy and we need to change the root config file
    ex_defaults = idleConf.defaultCfg["extensions"].file
    if has_user:
        # Otherwise, idleuserextend patches IDLE and we only need to modify
        # the user config file
        ex_defaults = idleConf.userCfg["extensions"].file
        extensions |= set(idleConf.userCfg["extensions"])

    # Import this extension (this file),
    module = __import__(__title__)

    # Get extension class
    if not hasattr(module, __title__):
        print(
            f"ERROR: Somehow, {__title__} was installed improperly, "
            f"no {__title__} class found in module. Please report "
            "this on github.",
            file=sys.stderr,
        )
        sys.exit(1)

    cls = getattr(module, __title__)

    # Get extension class keybinding defaults
    required_config = get_required_config(
        getattr(cls, "values", {}),
        getattr(cls, "bind_defaults", {}),
    )

    # If this extension not in there,
    if __title__ not in extensions:
        # Tell user how to add it to system list.
        print(f"{__title__} not in system registered extensions!")
        print(
            f"Please run the following command to add {__title__} "
            + "to system extensions list.\n",
        )
        # Make sure line-breaks will go properly in terminal
        add_data = required_config.replace("\n", "\\n")
        # Tell them the command
        append = "| sudo tee -a"
        if has_user:
            append = ">>"
        print(f"echo -e '{add_data}' {append} {ex_defaults}\n")
    else:
        print(f"Configuration should be good! (v{__version__})")
        return True
    return False


def ensure_section_exists(section: str) -> bool:
    """Ensure section exists in user extensions configuration.

    Returns True if edited.
    """
    if section not in idleConf.GetSectionList("user", "extensions"):
        idleConf.userCfg["extensions"].AddSection(section)
        return True
    return False


def ensure_values_exist_in_section(
    section: str,
    values: dict[str, str],
) -> bool:
    """For each key in values, make sure key exists. Return if edited.

    If not, create and set to value.
    """
    need_save = False
    for key, default in values.items():
        value = idleConf.GetOption(
            "extensions",
            section,
            key,
            warn_on_default=False,
        )
        if value is None:
            idleConf.SetOption("extensions", section, key, default)
            need_save = True
    return need_save


def get_search_engine_params(
    engine: searchengine.SearchEngine,
) -> dict[str, str | bool]:
    """Get current search engine parameters."""
    return {
        name: getattr(engine, f"{name}var").get()
        for name in ("pat", "re", "case", "word", "wrap", "back")
    }


def set_search_engine_params(
    engine: searchengine.SearchEngine,
    data: dict[str, str | bool],
) -> None:
    """Get current search engine parameters."""
    for name in ("pat", "re", "case", "word", "wrap", "back"):
        if name in data:
            getattr(engine, f"{name}var").set(data[name])


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

    def load_prefs(self) -> None:
        """Load search engine preferences."""
        self.global_search_params = get_search_engine_params(self.engine)
        set_search_engine_params(self.engine, self.search_params)

    def store_prefs(self) -> None:
        """Restore global search engine preferences."""
        self.search_params = get_search_engine_params(self.engine)
        set_search_engine_params(self.engine, self.global_search_params)

    def open(  # noqa: A003  # Override for superclass we don't control
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

        try:
            first = text.index("sel.first")
        except TclError:
            first = None
        try:
            last = text.index("sel.last")
        except TclError:
            last = None
        first = first or text.index("insert")
        last = last or first

        super().open(text, searchphrase)

        self.extension.show_hit(first, last)

        self.insert_tags = insert_tags

    def close(self, event: Event[Any] | None = None) -> None:
        """Close the dialog and remove hit tags."""
        super().close(event)

        # Restore global search engine preferences
        self.store_prefs()

        self.extension.hide_hit()
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

    def default_command(self, event: Event[Any] | None = None) -> bool:
        """Handle align again as the default command."""
        if not self.engine.getpat():
            self.open()
            return False

        pattern = self.engine.getprog()
        if not pattern:
            return False

        space_wrap: bool = self.space_wrap_var.get()
        align_side: bool = self.align_side_var.get()

        close = self.extension.align_selected(
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


def get_whole_line(selection: str, add: int = 0) -> str:
    """Get whole line of selection and add to line number."""
    line = searchengine.get_line_col(selection)[0]
    return f"{line + add}.0"


# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.


class idlealign:  # noqa: N801  # Class name must match extension module name
    """Add comments from mypy to an open program."""

    __slots__ = ("editwin", "text")
    # Extend the file and format menus.
    menudefs: ClassVar = [
        ("format", [("Align Selection", "<<align-selection>>")]),
    ]
    # Default values for configuration file
    values: ClassVar = {
        "enable": "True",
        "enable_editor": "True",
        "enable_shell": "False",
    }
    # Default key binds for configuration file
    bind_defaults: ClassVar = {
        "align-selection": "<Alt-Key-a>",
    }

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        """Initialize the settings for this extension."""
        self.editwin = editwin
        self.text: Text = editwin.text

    @property
    def window(self) -> AlignDialog:
        """Window for current text widget."""
        return self.create_window()

    @classmethod
    def ensure_bindings_exist(cls) -> bool:
        """Ensure key bindings exist in user extensions configuration.

        Return True if need to save.
        """
        if not cls.bind_defaults:
            return False

        need_save = False
        section = f"{cls.__name__}_cfgBindings"
        if ensure_section_exists(section):
            need_save = True
        if ensure_values_exist_in_section(section, cls.bind_defaults):
            need_save = True
        return need_save

    @classmethod
    def ensure_config_exists(cls) -> bool:
        """Ensure required configuration exists for this extension.

        Return True if need to save.
        """
        need_save = False
        if ensure_section_exists(cls.__name__):
            need_save = True
        if ensure_values_exist_in_section(cls.__name__, cls.values):
            need_save = True
        return need_save

    @classmethod
    def reload(cls) -> None:
        """Load class variables from configuration."""
        # Ensure file default values exist so they appear in settings menu
        save = cls.ensure_config_exists()
        if cls.ensure_bindings_exist() or save:
            idleConf.SaveUserCfgFiles()

        # Reload configuration file
        idleConf.LoadCfgFiles()

        # For all possible configuration values
        for key, default in cls.values.items():
            # Set attribute of key name to key value from configuration file
            if key not in {"enable", "enable_editor", "enable_shell"}:
                value = idleConf.GetOption(
                    "extensions",
                    cls.__name__,
                    key,
                    default=default,
                )
                setattr(cls, key, value)

    def create_window(self) -> AlignDialog:
        """Create align dialog window."""
        root: Tk
        root = self.text._root()  # type: ignore[attr-defined]

        engine: searchengine.SearchEngine = searchengine.get(root)

        if not hasattr(engine, "_aligndialog"):
            engine._aligndialog = AlignDialog(root, engine, self)
        return cast(AlignDialog, engine._aligndialog)

    def show_hit(self, first: str, last: str) -> None:
        """Highlight text between first and last indices.

        Text is highlighted via the 'hit' tag and the marked
        section is brought into view.

        The colors from the 'hit' tag aren't currently shown
        when the text is displayed.  This is due to the 'sel'
        tag being added first, so the colors in the 'sel'
        configuration are seen instead of the colors for 'hit'.
        """
        text = self.text
        text.mark_set("insert", first)
        text.tag_remove("sel", "1.0", "end")
        text.tag_add("sel", first, last)
        text.tag_remove("hit", "1.0", "end")
        if first == last:
            text.tag_add("hit", first)
        else:
            text.tag_add("hit", first, last)
        text.see("insert")
        text.update_idletasks()

    def hide_hit(self) -> None:
        """Hide hit after show_hit."""
        self.text.tag_remove("hit", "1.0", "end")

    def align_selected(
        self,
        pattern: Pattern[str],
        space_wrap: bool = True,
        align_side: bool = False,
        tags: str | list[str] | tuple[str, ...] = (),
    ) -> bool:
        """Align selected text by pattern. Side False == left.

        Return True if should close window.
        """
        # Get start and end from selection, both are strings of {line}.{col}
        select_start, select_end = searchengine.get_selection(self.text)

        # Get full first line till one past end line from selection
        select_start = get_whole_line(select_start)
        grab_end = get_whole_line(select_end, 1)

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
        self.text.undo_block_start()  # type: ignore[attr-defined]

        # Replace old text with new aligned text
        self.text.delete(select_start, grab_end)
        self.text.insert(select_start, chars, tags)

        self.text.undo_block_stop()  # type: ignore[attr-defined]

        # Select modified area
        self.show_hit(select_start, select_end)
        return True

    def align_selection_event(self, event: Event[Any] | None) -> str:
        """Align selected text."""
        # pylint: disable=unused-argument
        self.reload()

        self.window.open()
        return "break"


idlealign.reload()

if __name__ == "__main__":
    print(f"{__title__} v{__version__}\nProgrammed by {__author__}.\n")
    check_installed()
