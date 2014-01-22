import sublime, sublime_plugin
import sys, types, os, json
from copy import deepcopy

def settings():
    return sublime.load_settings(settings_file_name())

def settings_file_name():
    if sys.platform.startswith('linux'):
        return 'AcmePlumbing (Linux).sublime-settings'
    elif sys.platform == 'darwin':
        return 'AcmePlumbing (OSX).sublime-settings'
    elif sys.platform == 'win32':
        return 'AcmePlumbing (Windows).sublime-settings'
    else:
        # fall back to settings that may work for the system...
        # most likely something posixy running X?
        return 'AcmePlumbing (Linux).sublime-settings'

def add_rule(key, comment, rule):
    """
    Add a rule to the user settings

    Rules are saved in this format:

    // key
    // comment
    [
        "rule"
    ],

    The key is used to determine whether the rule can be replaced in place, or if it has to be inserted into
    the pipeline. New rules are placed at the very top.

    The user settings are used because it gives the user the best control and visibility about their plumbing.
    This way they can see the extra rule and move/delete it

    Since the json encoder and decoder can't preserve comments I am manually parsing the settings file. Not
    exactly pleasant and prone to breaking

    """
    key = "// " + key
    user_settings = os.path.join(sublime.packages_path(),'User',settings_file_name())

    # if no user settings exist, copy the default settings so the user still has the
    # default pipeline.
    if not os.path.isfile(user_settings):
        default_settings = os.path.join(sublime.packages_path(),'User',settings_file_name())
        shutil.copysile(default_settings, file_name)

    lines = [] # all lines in the settings file
    rule_section = [] # lines for the current rule

    # convert the rule into pretty printed json
    # a trailing comma is appended so it can be inserted before a rule without
    # breaking the settings file. The parser for settings seems to ignore the
    # comma at the end without any fuss
    rule_json = (json.dumps(rule, sort_keys=True,
                     indent=4, separators=(',', ': ')) + ',').splitlines()
    indent = "        " # 2 indents @ 4 spaces
    rule_section.append(indent + key + "\n")
    rule_section.append(indent + "// " + comment + "\n")
    for line in rule_json:
        rule_section.append(indent + line + "\n")

    replaced = False

    # open the settings and replace the rule with the current
    # rule pipeline.
    with open(user_settings, 'r') as sf:
        for line in sf:
            if line.strip() == key:
                whitespace = line[:len(line) - len(line.lstrip())]
                # skip to the end of the rule
                for count,line in enumerate(sf):
                    if line.strip() == "],": break
                # inject the new rule data
                lines.extend(rule_section)
                replaced = True
            else:
                lines.append(line)

    # if the original rule is not replaced, insert it at the top
    if not replaced:
        pos = 0
        for count,line in enumerate(lines):
            if line.strip() == '"rules": [':
                pos = count + 1 # next line after 'rules'
                break

        lines = lines[:pos] + rule_section + lines[pos:]

    # save the new settings file
    with open(user_settings, 'w') as sf:
        sf.writelines(lines)

    # finally display the new pipeline to the user
    # TODO: highlight the new rule
    sublime.active_window().open_file(user_settings)

def get_rules():
    """ Return the current list of rules """
    return settings().get("rules", [])

def get_commands():
    return dict({}
       |get_module_methods('SublimeAcmePlumbing.Commands').items()
       |get_module_methods('User.AcmePlumbingCommands').items()
       )

def get_command(name):
    return get_commands().get(name, None)

def get_module_methods(module_name):
    """ Return a dictionary of all module level functions"""
    if module_name not in sys.modules:
        try:
            __import__(module_name)
        except ImportError:
            if not module_name.startswith("User."):
                print("Could not load: " + module_name)
            return {}

    module = sys.modules[module_name]
    methods = {}
    for k,v in module.__dict__.items():
        if isinstance(v, types.FunctionType):
            methods[k] = v

    return methods

class AcmePlumbing(sublime_plugin.TextCommand):
    """ Run a message through the plumbing """
    def run_(self, edit_token, original_message):
        # using run_ instead of run, as run will explode the
        # message into multiple keyword arguments, and I don't feel like
        # wrapping it in a dict
        edit = self.view.begin_edit(edit_token, self.name(), original_message)
        original_message["edit_token"] = edit

        try:
            all_rules= get_rules()
            for rule in all_rules:
                matched = True
                pipeline_data = {}

                # clone the original message so a pipeline can modify the message
                # without affecting the next rule if it fails
                message = deepcopy(original_message)

                for definition in rule:
                    # allow plain strings to just call a command without any args
                    # otherwise the first item is the command name
                    # and the rest are the args
                    # mokes the config less verbose
                    name = None
                    args = []
                    if isinstance(definition, str):
                        name = definition
                    else:
                        name = definition[0]
                        args = definition[1:]

                    # run the selected test and save its results
                    command = get_command(name)
                    if command:
                        # if a test errors, assume it has failed
                        results = False
                        try:
                            results = command(message, args, pipeline_data)
                        except Exception as e:
                            # hopefully log it?
                            print(e)
                        finally:
                            if results:
                                pipeline_data[name] = results
                            else:
                                matched = False
                                break

                if matched: break
        finally:
            self.view.end_edit(edit)
