# AcmePlumbing
> Make your text clickable

# What

+ Right click on https://www.google.com/search?q=Acme+Editor and a google search is opened in your browser.
+ Right click on Actions.py@prepare_command and Actions.py is opened at the definition for prepare_command. 
+ Right click on pydoc(re) to see help on python regular expressions. 
+ Right click on shutdown and your computer turns off (causing you to wonder why you set up that last one).

# Why

I played with Acme Editor and found the way it considered text to be part of the UI fun. However I wanted to play with it in an environment that I was more comfortable in (and runs nicely on Windows). Besides, I *really* wanted to be able to link files together as an adhoc wiki.

# How

The selected text is placed into a message as the data. It is then passed to two pipelines: match, and actions.

The match pipeline tests the message to see if it can hand it over to the actions pipeline. It also gathers extra data for the actions pipeline (e.g. is_file gathers the full file name if the data is a relative file).

If every command in the match pipeline passes, the message is passed on to the actions pipeline. The actions pipeline runs all the commands.

NOTE: commands in the pipeline are free to modify the message (if the match pipeline fails, the message is set back to the original for the next set of match rules)

# Configuration

> see Default.sublime-settings

Rules pairs of match rules and actions, corresponding to each pipeline.

```json
{"match": [ ], "actions":[ ] }
```

Each pipeline is a list of commands to run. You can pass extra arguments to each command by wrapping it in a list. The first item is the command name and the remainder are the arguments.

```json
{"match": [ "is_file", [ "pattern", "\.txt$"] ], "actions": [ ] }
```

This rule will match any png file that exists on the disk. Since there are no actions, nothing will happen.

```json
{"match": [ "is_file", [ "pattern", "\.txt$"] ], "actions": [ "open_in_tab" ] }
```
Now when the name for a real txt file is right clicked it will be opened in a new tab.

The pipelines can modify the message as it passes through the commands. This can be seen in the prepare_command action.

## Tests

These commands can be used in the match pipeline

### pattern

> see Tests.py@pattern

Runs the data against a regular expression specified in the second argument. The results are stored in the match\_data allowing the action pipeline to use segments of the data.

### is_file

> see Tests.py@is_file

is_file tests if the message data references a file. If it fails, it tries again as a relative path using the current working directory set in the message. The final path is stored in the match\_data to allow subsequent actions access to the full path

### is_dir

> see Tests.py@is_dir

is_dir tests if the message data references a directory. Like is_file, if it fails it tries again as a relative path using the current working directory set in the message. The final path is stored in the match\_data to allow subsequent actions access to the full path.


### extract_jump

> see Tests.py@extract_jump

This test is different as it will always pass. It's purpose is to remove jump locations form the data and store them somewhere separate (match\_data) so they don't interfere with subsequent tests. This is important as keeps stops is_file from having to be aware of how to jump to a location in a file, and it can focus on just testing if a file exists

> see Actions.py@jump for the syntax used to jump

## Actions

These commands are used in the actions pipeline

### prepare_command

> see Actions.py@prepare_command

prepare_command replaces text in the data based off the results of the match pipeline. At its most basic $\_ is replaced with the contents of the message data (the text that you clicked on).

#### pattern

Results from the pattern test can be replaced by either referencing them by their group position (e.g. $1) or by the group name (e.g. $section)

#### is_file / is_dir

The result of is_file and is_dir can be accessed with $\_ replacing it with the full path to the file. NOTE: this is instead of the contents of message data.

### open\_in\_tab

> see Actions.py@open\_in\_tab

open\_in\_tab opens whatever is in message['data'] in a new tab. If a file exists with that path it will open that file. Otherwise it will assume that the data is a shell command. It will run the command and if there is output it will be placed in a new tab. An example of this is the rule to open man pages.

### jump

> see Actions.py@jump

jump uses the results from extract_jump and moves the cursor to a new location. It uses syntax similar to Go To Anything:

* __@__ jump to symbol 
* __#__ jump to text
* __:__ jump to line

### open\_in\_external_process

> see Actions.py@open\_in\_external_process

open\_in\_external_process assumes that the message data is a command and runs it. No new tabs are opened. This is primarily used for rules like URLs where you want them to open in your browser, not your text editor.

# Extending

## Message

The structure of the message looks like

```json
{
  "data": "the selected text",
  "cwd": "the parent directory of the current file"
  "src": "the view id",
  "edit_token": "the edit token used for editing views"
}
```

## Creating new actions

You can add custom actions by creating them in AcmePlumbingActions.py in your user directory. Each action is a function with the signature:

```python
def custom_action(message, arguments, match_data):
    pass
```

You can then reference them by the function name in your rule set:

```json
{"match": [ ], "actions": [ "custom_action" ]}
```

## Creating new tests

Tests are added like new actions. Their file is AcmePlumbingTests.py. The signature is

```python
def custom_test(message, arguments):
    pass
```

The return value of your test will be placed in match_data with the same key as the name of your function. If you return a false value the test will not be considered to be passed and the actions will not run.

## Calling from another plugin

There is a small api to allow other plugins to inject new rules, actions, and tests. These have higher priority than the default settings, but lower than anything user defined.

They are in the AcmePlumbing module:

These add new plumbing

```
add_rule(rule)
add_test(name, test)
add_action(name, action)
```
add\_test and add\_action take a function as their second argument that should match the signature in the creating new tests/actions sections

These remove plumbing

```
remove_rule(rule)
remove_test(name)
remove_action(name)
```
You can only remove plumbing that was added with the previous add commands.



Consider this example:

```python
import sublime
from AcmePlumbing import SublimePlumb

def always(message, args):
    return True

def greet(message, args, match_data):
    window = sublime.active_window()
    tab = window.new_file()
    tab.set_scratch(True)
    edit_token = message['edit_token']
    tab.insert(edit_token, 0, "Hello. How's the weather?")

def plugin_loaded():
    AcmePlumbing.add_test("always", always)
    AcmePlumbing.add_action("greet", greet)
    AcmePlumbing.add_rule({"match":[
                               "always"
                           ],
                           "actions": [
                               "greet"
                            ]})
```


This plugin sets up the plumbing so that anything you right click on will open a new tab asking you about the the weather
