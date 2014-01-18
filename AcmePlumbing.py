import sublime, sublime_plugin
import sys, types
from copy import deepcopy

# variables used to store transient rules, and commands
# the idea is that other plugins can add to them without affecting
# the base and user defined sets
_rules = []
_commands = {}

def settings():
    if sys.platform.startswith('linux'):
        return sublime.load_settings('AcmePlumbing (Linux).sublime-settings')
    elif sys.platform == 'darwin':
        return sublime.load_settings('AcmePlumbing (OSX).sublime-settings')
    elif sys.platform == 'win32':
        return sublime.load_settings('AcmePlumbing (Windows).sublime-settings')
    else:
        # fall back to settings that may work for the system...
        # most likely something posixy running X?
        return sublime.load_settings('AcmePlumbing (Linux).sublime-settings')

def add_rule(rule):
    """ Add a rule to the base list. This has the lowest priority and does not get saved """
    _rules.insert(0, rule)

def remove_rule(rule):
    """ Remove a rule from the base list """
    _rules.remove(rule)

def get_rules():
    """ Return the current list of rules """
    return _rules + settings().get("rules", [])

def get_commands():
    return dict({}
       |get_module_methods('SublimeAcmePlumbing.Commands').items()
       |_commands.items()
       |get_module_methods('User.AcmePlumbingCommands').items()
       )

def get_command(name):
    return get_commands().get(name, None)

def remove_command(name):
    """ Remove an action from the base list """
    del _command[name]


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
