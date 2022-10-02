#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Idle Align - Emacs Align by Regular Expression as an IDLE Extension

"IDLE Extension to Align by Regular Expression"

# Programmed by CoolCat467

from __future__ import annotations

__title__     = 'idlealign'
__author__    = 'CoolCat467'
__license__   = 'GPLv3'
__version__   = '0.0.1'
__ver_major__ = 0
__ver_minor__ = 0
__ver_patch__ = 1

from typing import Optional

import sys
from re import Pattern

from tkinter            import BooleanVar, Event, TclError, Tk, Widget
from tkinter.ttk        import Checkbutton, Frame, Label, Radiobutton

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

##def setup(extension: 'idlealign') -> 'AlignDialog':
##    """Return the new or existing singleton AlignDialog instance.
##
##    The singleton dialog saves user entries and preferences
##    across instances.
##
##    Arguments:
##        text: Text widget containing the text to be aligned.
##    """
##    text: Widget = extension.text
##    root: Tk
##    root = text._root()# type: ignore
##
##    engine: searchengine.SearchEngine = searchengine.get(root)
##    if not hasattr(engine, '_aligndialog'):
##        engine._aligndialog = AlignDialog(root, engine, extension)
##    return engine._aligndialog
##
####def align_selection(text: Widget) -> None:
##    """Align by the selected pattern in the text.
##
##    Module-level function to access the singleton AlignDialog
##    instance to align again using the user entries and preferences
##    from the last dialog.  If there was no prior alignment, open the
##    align dialog; otherwise, perform the alignment without showing the
##    dialog.
##    """
##    setup(text).open(text)

def get_search_engine_params(engine: searchengine.SearchEngine) -> dict[str, str | bool]:
    "Get current search engine parameters"
    return {
        name: getattr(engine, f'{name}var').get()
        for name in ('pat', 're', 'case', 'word', 'wrap', 'back')
    }

def set_search_engine_params(engine: searchengine.SearchEngine,
                             data: dict[str, str | bool]) -> None:
    "Get current search engine parameters"    
    for name in ('pat', 're', 'case', 'word', 'wrap', 'back'):
        if name in data:
            getattr(engine, f'{name}var').set(data[name])

class AlignDialog(SearchDialogBase):
    "Dialog for aligning by a pattern in text."
    title          = 'Align Dialog'
    icon           = 'Align'
    needwrapbutton = False

    def __init__(self,
                 root: Tk,
                 engine: searchengine.SearchEngine,
                 extension: 'idlealign') -> None:
        """Create search dialog for aligning text

        Uses SearchDialogBase as the basis for the GUI and a
        searchengine instance to prepare the search.

        Attributes:
            space_wrap_var: BooleanVar of if the align text should be wrapped with spaces
            insert_tags: Optional string of tags for text insert
            extension: Extension class
            prev_search_params: Dictionary of search parameters before opening window
        """
        super().__init__(root, engine)
        self.insert_tags: Optional[str] = None

        self.space_wrap_var = BooleanVar(root, True) # Space wrap alignment pattern?
        self.align_side_var = BooleanVar(root, False) # Alignment side var
        
        self.extension = extension
        
        self.global_search_params: dict[str, str | bool]
        self.search_params: dict[str, str | bool] = {
            'wrap': False,
            'back': False
        }
    
    def load_prefs(self) -> None:
        "Load search engine prefrences"
        self.global_search_params = get_search_engine_params(self.engine)
        set_search_engine_params(self.engine, self.search_params)
    
    def store_prefs(self) -> None:
        "Restore global search engine prefrences"
        self.search_params = get_search_engine_params(self.engine)
        set_search_engine_params(self.engine, self.global_search_params)

    def open(self,
             searchphrase: Optional[str] = None,
             insert_tags : Optional[str] = None) -> None:
        """Make dialog visible on top of others and ready to use.

        Also, highlight the currently selected text.

        Arguments:
            text: Text widget being searched.
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
        
        if first is None or last is None:
            self.bell()
            self.store_prefs()
            return
        
        super().open(text, searchphrase)
        
        self.extension.show_hit(first, last)
        
        self.insert_tags = insert_tags

    def close(self, event: Event=None) -> None:
        "Close the dialog and remove hit tags."
        super().close(event)
        
        # Restore global search engine prefrences
        self.store_prefs()
        
        self.extension.hide_hit()
        self.insert_tags = None

    def create_option_buttons(self) -> tuple[Frame, list[tuple[BooleanVar, str]]]:
        "Create option buttons."
        frame: Frame
        base_options: list[tuple[BooleanVar, str]]
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
        "Override so Search Direction is instead Alignment Side"
        frame = self.make_frame('Alignment Side')[0]
        var = self.align_side_var
        others = [(False, 'Left'), (True, 'Right')]
        for val, label in others:
            btn = Radiobutton(frame, variable=var, value=val, text=label)
            btn.pack(side="left", fill="both")
        return frame, others

    def create_command_buttons(self) -> None:
        "Create command buttons."
        super().create_command_buttons()
        self.make_button("Align", self.default_command, isdef=True)

    def default_command(self, event: Event = None) -> bool:
        "Handle align again as the default command."
        if not self.engine.getpat():
            self.open()
            return False

        pattern = self.engine.getprog()
        if not pattern:
            return False
        
        space_wrap: bool = self.space_wrap_var.get()
        align_side: bool = self.align_side_var.get()
        
        close = self.extension.align_selected(
            pattern, space_wrap, align_side, self.insert_tags
        )
        
        if close:
            # Close window
            self.close()
        else:
            # Ring bell because something went wrong
            self.bell()
        return close

def get_whole_line(selection: str, add: int = 0) -> str:
    "Get whole line of selection (set column to zero) and add to line number"
    line = searchengine.get_line_col(selection)[0]
    return f'{line + add}.0'

# Important weird: If event handler function returns 'break',
# then it prevents other bindings of same event type from running.
# If returns None, normal and others are also run.

class idlealign:# pylint: disable=invalid-name
    "Add comments from mypy to an open program."
    __slots__ = (
        'editwin',
        'text',
        'window'
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
        self.editwin      = editwin
        self.text: Widget = editwin.text
        self.window       = self.create_window()

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

    def create_window(self) -> AlignDialog:
        "Create window"
        root: Tk
        root = self.text._root()# type: ignore

        engine: searchengine.SearchEngine = searchengine.get(root)

        if not hasattr(engine, '_aligndialog'):
            engine._aligndialog = AlignDialog(root, engine, self)
        return engine._aligndialog
    
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
    
    def hide_hit(self) -> None:
        "Hide hit aftere show_hit"
        self.text.tag_remove("hit", "1.0", "end")
    
    def align_selected(self,
                       pattern: Pattern,
                       space_wrap: bool = True,
                       align_side: bool = False,
                       tags: Optional[str] = None) -> bool:
        "Align selected text by pattern. Side False == left. Return True if should close window."
        # Get start and end from selection, both are strings of {line}.{col}
        select_start, select_end = searchengine.get_selection(self.text)

        # Get full first line till one past end line from selection
        select_start = get_whole_line(select_start)
        grab_end     = get_whole_line(select_end, 1)

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
            
            if match is None:# If align pattern not in line, skip line
                continue
            
            # Get the where alignment pattern starts and ends at
            start, end = match.span()
            
            prefix = line[:start]
            align = line[start:end]
            suffix = line[end:]
            
            # If space wrap is set, wrap alignment text with spaces
            if space_wrap:
                align = f' {align} '
            
            if not align_side: # If align to left side
                # Strip trailing spaces before align but keep indent
                prefix = prefix.rstrip()
                suffix = align + suffix.strip() # Strip extra spaces
            else: # If align to right side
                prefix += align.lstrip()
                suffix = suffix.lstrip()
            
            line_data[idx] = (prefix, suffix) # Remember after we get max

            sec_start = max(sec_start, len(prefix)) # Update max

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
        lines.append('')
        # Re-get characters to set
        chars = '\n'.join(lines)

        # This is all one operation
        self.text.undo_block_start()

        # Replace old text with new aligned text
        self.text.delete(select_start, grab_end)
        self.text.insert(select_start, chars, tags)

        self.text.undo_block_stop()

        # Select modified area
        self.show_hit(select_start, select_end)
        return True

    def align_selection_event(self, event: Event) -> str:
        "Align selected text"
        self.reload()

        self.window.open()
        return 'break'

idlealign.reload()

if __name__ == '__main__':
    print(f'{__title__} v{__version__}\nProgrammed by {__author__}.\n')
    check_installed()
