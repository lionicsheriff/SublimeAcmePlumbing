import sublime, sublime_plugin, os
from sublime import Region
from subprocess import Popen, PIPE

pmessage = {
    "src": "sublime-text-3",
    "dst": "???",
    "wdir": "parent dir for file?",
    "type": "text",
    "data": "file name"
}

Plumbing = {
    "variables": {
        "protocol": "^(https?|ftp|file|mailto)",
        "file": "([:.][a−zA−Z0−9_?,%#~&/\−]+)*"
    },
    "rules": [
        {
        # matches refine the data i.e. the result of prev match
        # is used if possible. That way you can construct simpler
        # expressions. They must all match though.

            "matches": [
                '[a-zA-Z0-9_\-./]+',
                '([a−zA−Z0−9_\−./]+).(jpe?g|gif|png)'
            ],
            "start": "feh $file"
        },
        {
            "matches": [
                "(?P<page>[a-zA-Z0-9_\-./]+)\((?P<section>[0-9])\)"
            ],
            "open": "man -P cat $page $section"
        }
    ]
}

class AcmeMouse(sublime_plugin.TextCommand):
    last_selection = {
        1: [],
        2: [],
        3: []
    }

    def selection_at_cursor(self):
        selection = self.view.sel()[0]
        if selection.b - selection.a == 0:

            contains = [s for s in AcmeMouse.last_selection[1] if s.a <= selection.a and s.b >= selection.b]
            if len(contains) > 0:
                selection = contains[0]
            else:
                selection = self.expand_selection(selection)

        return selection


    def expand_selection (self, pos):
        settings = self.view.settings()
        old_boundaries = settings.get("word_separators")
        settings.set("word_separators"," <>|(){};")
        expanded_selection = self.view.word(pos)
        settings.set("word_separators", old_boundaries)
        return expanded_selection


class AcmeGo(AcmeMouse):
    def run(self, edit):
        AcmeMouse.last_selection[1] = []

class AcmeRun(AcmeMouse):
    class CommandTypes:
        PIPE = 0
        SILENT = 1
        NORMAL = 2

    def run(self, edit):
        command = self.selection_at_cursor()
        type = self.get_command_type(command)
        out, err = self.run_command(self.view.substr(command), type)

        if out == None:
            return

        out = out.decode(encoding='utf-8')

        if type == self.CommandTypes.PIPE:
            sel = AcmeMouse.last_selection[1][0]
            self.view.replace(edit, sel, out)
        else:
            last_char = self.view.size()
            self.view.insert(edit, last_char, "\n" + out)

        AcmeMouse.last_selection[1] = []

    def get_command_type(self, selection):
        first_char = self.view.substr(Region(selection.a, selection.a + 1))
        prev_char = self.view.substr(Region(selection.a - 1, selection.a))

        for char in [first_char, prev_char]:
            if char == "|" :
                return self.CommandTypes.PIPE
            elif char == ">":
                return self.CommandTypes.SILENT

        return self.CommandTypes.NORMAL

    def run_command(self, command, type):
        if not command or (type == self.CommandTypes.PIPE and len(AcmeMouse.last_selection[1]) == 0):
            return None

        cwd = "~"
        file_name = self.view.file_name()
        if (file_name):
            cwd = os.path.dirname(file_name)

        p = Popen([command], shell=True, stdin=PIPE, stdout=PIPE, cwd=cwd)
        if type == self.CommandTypes.PIPE:
            stdin = self.view.substr(AcmeMouse.last_selection[1][0])
            stdin.encode('utf-8')
            return p.communicate(input=str.encode(stdin))
        if type == self.CommandTypes.SILENT:
            return None
        else :
            return p.communicate()


        # ls -lh
        # |md5sum
        # md5sum

class AcmeSelect(sublime_plugin.TextCommand):
    def run_(self, edit_token, args):
        event = args['event']
        AcmeMouse.last_selection[event["button"]] = [r for r in self.view.sel()]
        print (AcmeMouse.last_selection)