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

    def get_selection(self, mouseButton):
        settings = self.view.settings()
        key = "SublimePlumb-mouse" + mouseButton
        return settings.get(key, [])

    def save_selection(self, mouseButton, selection):
        settings = self.view.settings()
        key = "SublimePlumb-mouse" + mouseButton
        settings.set(key, selection)

    def selection_at_cursor(self):
        selection = self.view.sel()[0]
        if selection.b - selection.a == 0:

            contains = [s for s in self.get_selection("1")
                        if s["a"] <= selection.a
                        and s["b"] >= selection.b]

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
        pass

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
            sel = self.get_selection("1")[0]
            region = sublime.Region(int(sel["a"]), int(sel["b"]))
            self.view.replace(edit, region, out)
        else:
            last_char = self.view.size()
            self.view.insert(edit, last_char, "\n" + out)

        self.save_selection("1", [])
        self.view.sel().clear()

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
        selection = self.get_selection("1")

        if not command or (type == self.CommandTypes.PIPE and len(selection) == 0):
            return None

        cwd = "~"
        file_name = self.view.file_name()
        if (file_name):
            cwd = os.path.dirname(file_name)

        p = Popen([command], shell=True, stdin=PIPE, stdout=PIPE, cwd=cwd)
        if type == self.CommandTypes.PIPE:
            inputRegion = sublime.Region(selection[0]["a"], selection[0]["b"])
            stdin = self.view.substr(inputRegion)
            stdin.encode('utf-8')
            return p.communicate(input=str.encode(stdin))
        if type == self.CommandTypes.SILENT:
            return None
        else :
            return p.communicate()


class AcmeSelect(AcmeMouse):
    def run_(self, edit_token, args):
        event = args['event']
        selection = [{"a": r.a, "b": r.b}
                     for r in self.view.sel()]
        self.save_selection(str(event["button"]), selection)

# Tests:        
# ls -lh
# |md5sum
# md5sum