# AcmePlumbing
> Make your text clickable

# What

+ Right click on https://www.google.com/search?q=Acme+Editor and a google search is opened in your browser.
+ Right click on Commands.py@prepare_command and Commands.py is opened at the definition for prepare_command. 
+ Right click on pydoc(re) to see help on python regular expressions. 
+ Right click on shutdown and your computer turns off (causing you to wonder why you set up that last one).

# Why

I played with Acme Editor and found the way it considered text to be part of the UI fun. However I wanted to play with it in an environment that I was more comfortable in (and runs nicely on Windows). Besides, I *really* wanted to be able to link files together as an adhoc wiki.

# How

Select text with the rigth mouse button. The selected text is placed into a message as the data and is then passed to a set of commands (a rule). The commands are evaluated from the first to the last, and if one fails the rule stops processing and the next rule is tried.

If you only want to select a word, you can save effort by just right clicking in the middle of the word. This will cause AcmePlumbing to expand the selection along the word boundaries.


# Configuration

> see AcmePlumbing (Linux).sublime-settings

Each rule is a list of commands to run. You can pass extra arguments to a command by wrapping it in a list.

```json
[
  "is_file",
  [ "pattern", "\.txt$"],
  "open_in_tab"
]
```

When a message is passed to this rule, the first commands checks that the message data refers to a file. If it is a file the next command is run, otherwise the rule exits. The second command then checks the message data against a regular expression. This command takes the regular expression as an argument. In this case it tests if the file is a .txt file. If that passes, the message is handed to the open_in_tab command, which opens the file referred to in the message data into a new tab.

NOTE: commands in the pipeline are free to modify the message (if the rule fails, the message is set back to the original for the next rule)

## Commands

### pattern

> see Commands.py@pattern

Runs the data against a regular expression specified in the second argument. The results are stored in the match\_data allowing the action pipeline to use segments of the data.

### is_file

> see Commands.py@is_file

is_file tests if the message data references a file. If it fails, it tries again as a relative path using the current working directory set in the message. The final path is stored in the match\_data to allow subsequent actions access to the full path

### is_dir

> see Commands.py@is_dir

is_dir tests if the message data references a directory. Like is_file, if it fails it tries again as a relative path using the current working directory set in the message. The final path is stored in the match\_data to allow subsequent actions access to the full path.


### extract_jump

> see Commands.py@extract_jump

This test is different as it will always pass. It's purpose is to remove jump locations form the data and store them somewhere separate (match\_data) so they don't interfere with subsequent tests. This is important as keeps stops is_file from having to be aware of how to jump to a location in a file, and it can focus on just testing if a file exists

> see Commands.py@jump for the syntax used to jump

### prepare_command

> see Commands.py@prepare_command

prepare_command replaces text in the data based off the results of the match pipeline. At its most basic $\_ is replaced with the contents of the message data (the text that you clicked on).

#### pattern

Results from the pattern test can be replaced by either referencing them by their group position (e.g. $1) or by the group name (e.g. $section)

#### is_file / is_dir

The result of is_file and is_dir can be accessed with $\_ replacing it with the full path to the file. NOTE: this is instead of the contents of message data.

### open\_in\_tab

> see Commands.py@open\_in\_tab

open\_in\_tab opens whatever is in message['data'] in a new tab. If a file exists with that path it will open that file. Otherwise it will assume that the data is a shell command. It will run the command and if there is output it will be placed in a new tab. An example of this is the rule to open man pages.

### jump

> see Commands.py@jump

jump uses the results from extract_jump and moves the cursor to a new location. It uses syntax similar to Go To Anything:

* __@__ jump to symbol 
* __#__ jump to text
* __:__ jump to line

### open\_in\_external_process

> see Commands.py@open\_in\_external_process

open\_in\_external_process assumes that the message data is a command and runs it. No new tabs are opened. This is primarily used for rules like URLs where you want them to open in your browser, not your text editor.

# Extending

## Message

The structure of the message looks like

```json
{
  "data": "the selected text",
  "cwd": "the parent directory of the current file",
  "src": "the view id",
  "edit_token": "the edit token used for editing views"
}
```

## Creating new commands

You can add custom commands by creating them in AcmePlumbingCommands.py in your user directory. Each action is a function with the signature:

```python
def custom_command(message, arguments, pipeline_data):
  return True
```

The command must return a true value if it succeeds. Otherwise the rule will be considered failed and the next rule will
be run.

You can then reference them by the function name in your rule set:

```json
[ "custom_command" ]
```

The return value is placed into pipeline_data, a dictionary that contains the results of all the previous commands in the rule.

## Calling from another plugin

There is a small api to allow other plugins to inject new rules, actions, and tests. These have higher priority than the default settings, but lower than anything user defined.

They are in the AcmePlumbing module:

These add new plumbing

```
add_rule(rule)
add_command(name, action)
```
add\_command takes a function as the second argument that should match the signature in the creating new command section. add\_rule takes a list exactly like the settings.

These remove plumbing

```
remove_rule(rule)
remove_command(name)
```
You can only remove plumbing that was added with the previous add commands.



Consider this example:

```python
import sublime
from SublimeAcmePluming import AcmePlumbing

def greet(message, args, match_data):
    window = sublime.active_window()
    tab = window.new_file()
    tab.set_scratch(True)
    edit_token = message['edit_token']
    tab.insert(edit_token, 0, "Hello. How's the weather?")
    return tab

def plugin_loaded():
    AcmePlumbing.add_action("greet", greet)
    AcmePlumbing.add_rule(["greet"])
```


This plugin sets up the plumbing so that anything you right click on will open a new tab asking you about the the weather
