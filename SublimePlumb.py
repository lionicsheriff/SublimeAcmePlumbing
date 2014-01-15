import sublime, sublime_plugin, os
from sublime import Region
from subprocess import Popen, PIPE
import re

pmessage = {
    "src": "sublime-text-3",
    "dst": "???",
    "wdir": "parent dir for file?",
    "type": "text",
    "data": "file name"
}


class AcmeMouse(sublime_plugin.TextCommand):

    @property
    def settings(self):
        return sublime.load_settings("SublimePlumb.sublime-settings")

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
        settings.set("word_separators"," ")
        expanded_selection = self.view.word(pos)
        settings.set("word_separators", old_boundaries)
        return expanded_selection

    
    class CommandTypes:
        PIPE = 0
        SILENT = 1
        NORMAL = 2

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

class AcmeGo(AcmeMouse):
    def run(self, edit):
        # mandb(8)
        # http://www.google.com
        # pydoc(re)
        selection = self.view.substr(self.selection_at_cursor())
        for rule in self.settings.get("rules"):
            pattern = rule["match"]
            print(pattern)
            print(selection)
            m = re.search(pattern, selection)
            if (m):
                print("matched: ", rule)
                if "open" in rule:
                    self.open(rule["open"], selection, m)

                if "start" in rule:
                    self.start(rule["start"], selection, m)

                break

    def generate_command(self, command, text, match):
        for idx, val in enumerate(match.groups()):
            group = idx + 1
            command = command.replace("$" + str(group), val)

        for group,val in match.groupdict().items():
            command = command.replace("$" + group, val)

        command = command.replace("$_", text)

        return command

    def open(self, command, text, match):
        command = self.generate_command(command, text, match)

    def start(self, command, text, match):
        command = self.generate_command(command, text, match)
        self.run_command(command, self.CommandTypes.SILENT)



class AcmeRun(AcmeMouse):

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
