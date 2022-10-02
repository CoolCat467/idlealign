#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Idle Align - Emacs Align by Regular Expression as an IDLE Extension

"IDLE Extension to Align by Regular Expression"

# Programmed by CoolCat467

from __future__ import annotations

__title__     = 'idlealign'
__author__    = 'CoolCat467'
__license__   = 'GPLv3'
__version__   = '0.0.0'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 0

from typing import Optional

import sys

from tkinter            import BooleanVar, Event, TclError, Tk, Widget
from tkinter.ttk        import Checkbutton, Frame, Label

from idlelib            import searchengine        # type: ignore
from idlelib.config     import idleConf            # type: ignore
from idlelib.pyshell    import PyShellEditorWindow # type: ignore
from idlelib.searchbase import SearchDialogBase    # type: ignore

def check_installed() -> bool:
    "Make sure extension installed."
    # Get list of system extensions
    extensions = list(idleConf.defaultCfg['extensions'])
    # If this extension not in there,
    if __title__ not in extensions:
        # Tell user how to add it to system list.
        print(f'{__title__} not in system registered extensions!')
        print(f'Please run the following command to add {__title__} to system extensions list.\n')
        ex_defaults = idleConf.defaultCfg['extensions'].file

        # Import this extension (this file),
        try:
            module = __import__(__title__)
        except ModuleNotFoundError:
            print(f'{__title__} is not installed!')
            return False
        # Get extension class
        if hasattr(module, __title__):
            cls = getattr(module, __title__)
            # Get extension class keybinding defaults
            add_data = ''
            if hasattr(cls, 'values'):
                # Get configuration defaults
                values = '\n'.join(f'{key} = {default}' for key, default in cls.values.items())
                # Add to add_data
                add_data += f"\n[{__title__}]\n{values}"
            if hasattr(cls, 'bind_defaults'):
                # Get keybindings data
                values = '\n'.join(f'{event} = {key}' for event, key in cls.bind_defaults.items())
                # Add to add_data
                add_data += f"\n[{__title__}_cfgBindings]\n{values}"
            # Make sure line-breaks will go properly in terminal
            add_data = add_data.replace('\n', '\\n')
            # Tell them command
            print(f"echo -e '{add_data}' | sudo tee -a {ex_defaults}")
            print()
        else:
            print(f'ERROR: Somehow, {__title__} was installed improperly, no {__title__} class '\
                  'found in module. Please report this on github.', file=sys.stderr)
            sys.exit(1)
    else:
        print(f'Configuration should be good! (v{__version__})')
        return True
    return False

def ensure_section_exists(section: str) -> bool:
    "Ensure section exists in user extensions configuration. Return True if created."
    if not section in idleConf.GetSectionList('user', 'extensions'):
        idleConf.userCfg['extensions'].AddSection(section)
        return True
    return False

def ensure_values_exist_in_section(section: str, values: dict[str, str]) -> bool:
    "For each key in values, make sure key exists. If not, create and set to value. "\
    "Return True if created any defaults."
    need_save = False
    for key, default in values.items():
        value = idleConf.GetOption('extensions', section, key,
                                   warn_on_default=False)
        if value is None:
            idleConf.SetOption('extensions', section, key, default)
            need_save = True
    return need_save

def setup(text: Widget) -> 'AlignDialog':
    """Return the new or existing singleton AlignDialog instance.

    The singleton dialog saves user entries and preferences
    across instances.

    Arguments:
        text: Text widget containing the text to be aligned.
    """
    root: Tk
    root = text._root()# type: ignore

    engine: searchengine.SearchEngine = searchengine.get(root)
    if not hasattr(engine, '_aligndialog'):
        engine._aligndialog = AlignDialog(root, engine)
    return engine._aligndialog

def align_selection(text: Widget) -> None:
    """Align by the selected pattern in the text.

    Module-level function to access the singleton AlignDialog
    instance to align again using the user entries and preferences
    from the last dialog.  If there was no prior alignment, open the
    align dialog; otherwise, perform the alignment without showing the
    dialog.
    """
    setup(text).open(text)

class AlignDialog(SearchDialogBase):
    "Dialog for aligning by a pattern in text."
    title          = 'Align Dialog'
    icon           = 'Align'
    needwrapbutton = False

    def __init__(self, root: Tk, engine: searchengine.SearchEngine) -> None:
        """Create search dialog for aligning text

        Uses SearchDialogBase as the basis for the GUI and a
        searchengine instance to prepare the search.

        Attributes:
            space_wrap_var: BooleanVar of if the align text should be wrapped with spaces
            insert_tags: Optional string of tags for text insert
        """
        super().__init__(root, engine)
        self.insert_tags: Optional[str] = None

        self.space_wrap_var = BooleanVar(root, True) # Space wrap alignment pattern?

        engine.revar.set(True)

    def show_hit(self, first: str, last: str) -> None:
        """Highlight text between first and last indices.

        Text is highlighted via the 'hit' tag and the marked
        section is brought into view.

        The colors from the 'hit' tag aren't currently shown
        when the text is displayed.  This is due to the 'sel'
        tag being added first, so the colors in the 'sel'
        config are seen instead of the colors for 'hit'.
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

    def open(self,
             text: Widget,
             searchphrase: Optional[str] = None,
             insert_tags : Optional[str] = None) -> None:
        """Make dialog visible on top of others and ready to use.

        Also, highlight the currently selected text.

        Arguments:
            text: Text widget being searched.
        """
        super().open(text)
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
        if first is None or last is None:
            self.bell()
            return
        self.show_hit(first, last)
        self.insert_tags = insert_tags

    def close(self, event: Event=None) -> None:
        "Close the dialog and remove hit tags."
        super().close(event)
        self.text.tag_remove("hit", "1.0", "end")
        self.insert_tags = None

    def create_option_buttons(self) -> tuple[Frame, list[Label]]:
        "Create option buttons."
        frame, base_options = super().create_option_buttons()
        options = [
            (self.space_wrap_var, "Space wrap")
        ]
        for var, label in options:
            btn = Checkbutton(frame, variable=var, text=label)
            btn.pack(side="left", fill="both")
            base_options.append((var, label))
        return frame, base_options

    def create_other_buttons(self) -> None:
        "Override so Search Direction area is not created."

    def create_command_buttons(self) -> None:
        "Create command buttons."
        super().create_command_buttons()
        self.make_button("Align", self.default_command, isdef=True)

    def default_command(self, event: Event = None) -> None:
        "Handle align again as the default command."
        self.align_again(self.text)

    def align_again(self, text: Widget) -> bool:
        """Repeat the last align.

        If no align was previously run, open a new search dialog.  In
        this case, no align is done.

        If a align was previously run, the align dialog won't be
        shown and the options from the previous align (including the
        align pattern) will be used to find the next occurrence
        of the pattern.  Next is relative based on direction.

        Position the window to display the located occurrence in the
        text.

        Return True if the search was successful and False otherwise.
        """
        align_by_text = self.engine.getpat()
        if not align_by_text:
            self.open(text)
            return False

        # If space wrap is set, wrap align by text with spaces
        if self.space_wrap_var.get():
            self.engine.setpat(f' {align_by_text} ')

        pattern = self.engine.getprog()
        if not pattern:
            # Restore original pattern if space wrapped
            if self.space_wrap_var.get():
                self.engine.setpat(align_by_text)
            return False

        # Get start and end from selection, both are strings of {line}.{col}
        select_start, select_end = searchengine.get_selection(text)

        # Get full first line till one past end line from selection
        select_start = select_start.split('.')[0]+'.0'
        grab_end = str(int(select_end.split('.')[0])+1)+'.0'

        # Get the characters from full line selection
        chars: str = text.get(select_start, grab_end)

        # Split lines
        lines = chars.splitlines()
        # Keeping track of lines to modify
        line_data: dict[int, tuple[str, int, int]] = {}

        # Finding min width excluding spaces of all lines till start of align pattern
        sec_start = 0
        for idx, line in enumerate(lines):
            # Regular expression match
            match = pattern.search(line)
            if match is None:# If align pattern not in line skip
                continue
            # Get the where align pattern starts and ends at
            start, end = match.span()

            strip = line[:start].rstrip() # Line till pattern start strip trailing spaces
            line = strip + line[start:] # Create new line after removeing spaces
            start = len(strip) # Start was resized

            line_data[idx] = (line, start, end) # Remember after we get max

            sec_start = max(sec_start, start) # Update max

        if not line_data:
            # There are no lines with selected pattern so bell and stop
            self.bell()
            # Restore original pattern if space wrapped
            if self.space_wrap_var.get():
                self.engine.setpat(align_by_text)
            return False

        # For each line selected that had align pattern, add or remove
        # spaces from start up to pattern so each pattern starts in the same column
        for key, value in line_data.items():
            line, start, end = value

            lines[key] = line[:start] + ' '*(sec_start - start) + line[start:end] + line[end:]
        # Add extra blank line because of how insert works
        lines.append('')
        # Re-get characters to set
        chars = '\n'.join(lines)

        # This is all one operation
        self.text.undo_block_start()

        # Replace old with new aligned
        text.delete(select_start, grab_end)
        text.insert(select_start, chars, self.insert_tags)

        self.text.undo_block_stop()

        # Select new area
        self.show_hit(select_start, select_end)

        # Restore original pattern if space wrapped
        if self.space_wrap_var.get():
            self.engine.setpat(align_by_text)
        self.close()
        return True

# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.

class idlealign:# pylint: disable=invalid-name
    "Add comments from mypy to an open program."
    __slots__ = (
        'editwin',
        'text'
    )
    # Extend the file and format menus.
    menudefs = [
        ('format', [
            ('Align Selection', '<<align-selection>>')
        ] )
    ]
    # Default values for configuration file
    values = {
        'enable'       : 'True',
        'enable_editor': 'True',
        'enable_shell' : 'False',
    }
    # Default key binds for configuration file
    bind_defaults = {
        'align-selection': '<Alt-Key-a>',
    }

    def __init__(self, editwin: PyShellEditorWindow) -> None:
        "Initialize the settings for this extension."
        self.editwin   = editwin
        self.text      = editwin.text

        for attrname in (a for a in dir(self) if not a.startswith('_')):
            if attrname.endswith('_event'):
                bind_name = '_'.join(attrname.split('_')[:-1]).lower()
                self.text.bind(f'<<{bind_name}>>', getattr(self, attrname))

    @classmethod
    def ensure_bindings_exist(cls) -> bool:
        "Ensure key bindings exist in user extensions configuration. Return True if need to save."
        need_save = False
        section = f'{cls.__name__}_cfgBindings'
        if ensure_section_exists(section):
            need_save = True
        if ensure_values_exist_in_section(section, cls.bind_defaults):
            need_save = True
        return need_save

    @classmethod
    def ensure_config_exists(cls) -> bool:
        "Ensure required configuration exists for this extension. Return True if need to save."
        need_save = False
        if ensure_section_exists(cls.__name__):
            need_save = True
        if ensure_values_exist_in_section(cls.__name__, cls.values):
            need_save = True
        return need_save

    @classmethod
    def reload(cls) -> None:
        "Load class variables from the extension settings."
##        # Ensure file default values exist so they appear in settings menu
##        save = cls.ensure_config_exists()
##        if cls.ensure_bindings_exist() or save:
##            idleConf.SaveUserCfgFiles()
        # For all possible configuration values
        for key, default in cls.values.items():
            # Set attribute of key name to key value from configuration file
            if not key in {'enable', 'enable_editor', 'enable_shell'}:
                value = idleConf.GetOption(
                    'extensions',
                    cls.__name__,
                    key,
                    default=default
                )
                setattr(cls, key, value)

    def align_selection_event(self, event: Event) -> str:
        "Align selected text"
        self.reload()
        align_selection(self.text)
        return 'break'

idlealign.reload()

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.\n')
    check_installed()
