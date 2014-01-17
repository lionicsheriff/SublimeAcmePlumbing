import sublime, sublime_plugin
import sys, types
from copy import deepcopy

# variables used to store transient rules, tests, and actions
# the idea is that other plugins can add to them without affecting
# the base and user defined sets
_rules = []
_tests = {}
_actions = {}

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

def match_rule(original_message):
    """ Return the first rule that matches the message """
    all_rules= get_rules()
    for rule in all_rules:
        matched = True
        match_data = {}

        # clone the original message so a pipeline can modify the message
        # without affecting the next rule if it fails
        message = deepcopy(original_message)

        for definition in rule['match']:
            # allow plain strings to just call a test without any args
            # otherwise the first item is the test name and the rest
            # are the args
            # mokes the config less verbose
            name = None
            args = []
            if isinstance(definition, str):
                name = definition
            else:
                name = definition[0]
                args = definition[1:]

            # run the selected test and save its results
            test = get_test(name)
            if test:
                # if a test errors, assume it has failed
                results = False
                try:
                    results = test(message, args)
                except Exception as e:
                    # hopefully log it?
                    print(e)
                finally:
                    if results:
                        match_data[name] = results
                    else:
                        matched = False
                        break

        if matched: return (message,rule, match_data)
    return (message,None, None)


def get_tests():
    """ Return a dictionary of the current set of tests """
    return dict({}
       |get_module_methods('SublimeAcmePlumbing.Tests').items()
       |_tests.items()
       |get_module_methods('User.AcmePlumbingTests').items()
    )

def get_test(name):
    """ Return the function associated to the named test """
    return get_tests().get(name, None)

def add_test(name, test):
    """ Add an test to the base list. This has the lowest priority and does not get saved """
    _tests[name] = test

def remove_test(name):
    """ Remove an test from the base list """
    del _tests[name]

def get_actions():
    """ Return a dictionary of the current set of actions """
    return dict({}
       |get_module_methods('SublimeAcmePlumbing.Actions').items()
       |_actions.items()
       |get_module_methods('User.AcmePlumbingActions').items()
    )

def get_action(name):
    """ Return the function associated to the named action """
    return get_actions().get(name, None)

def add_action(name, action):
    """ Add an action to the base list. This has the lowest priority and does not get saved """
    _actions[name] = action

def remove_action(name):
    """ Remove an action from the base list """
    del _actions[name]


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
    def run_(self, edit_token, message):
        # using run_ instead of run, as run will explode the
        # message into multiple keyword arguments, and I don't feel like
        # wrapping it in a dict
        edit = self.view.begin_edit(edit_token, self.name(), message)
        message["edit_token"] = edit

        try:
            message,rule,match_data = match_rule(message) # NOTE: the message gets mutated in the search pipeline
            if(rule):
                for definition in rule['actions']:
                    # like match rules, allow for an action to be declared as a
                    # plain string if no arguments are desired
                    name = None
                    args = []
                    if isinstance(definition, str):
                        name = definition
                    else:
                        name = definition[0]
                        args = definition[1:]

                    action = get_action(name)
                    if action:
                        action(message, args, match_data)
        finally:
            self.view.end_edit(edit)
