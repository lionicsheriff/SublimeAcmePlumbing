import sublime, os
from subprocess import Popen, PIPE

def open_in_tab(message, args, match_data):
    """ Opens a file, or output of a command in a new tab """
    cwd = message['cwd']
    command = message['data']
    window = sublime.active_window()

    if os.path.isfile(command):
        tab = window.open_file(command)
    else:
        p = Popen([command], shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if out:
            data = out.decode(encoding='utf-8')
            tab = window.new_file()
            tab.set_scratch(True)
            edit_token = message['edit_token']
            tab.insert(edit_token, 0, data)

def open_in_external_program(message, args, match_data):
    """ Starts an external program to view the message data """
    cwd = message['cwd']
    command = message['data']
    Popen([command], shell=True, cwd=cwd, close_fds=True)

def prepare_command(message, args, match_data):
    """ Munges the message data based off results of earlier match data """
    command = args[0]

    # replace group place holders
    # unnamed groups replace $groupnumber with the result
    #   e.g. $1
    # named groups use $groupname
    #   e.g. $file_name
    if "pattern" in match_data:
        match = match_data["pattern"]
        for idx, val in enumerate(match.groups()):
            group = idx + 1 # 0 is the full matched text
            command = command.replace("$" + str(group), val)

        for group,val in match.groupdict().items():
            command = command.replace("$" + group, val)

    # $_ is either the related file, or the original data
    if "is_file" in match_data:
        file_name = match_data["is_file"]
        command = command.replace("$_", file_name)
    elif "data" in message:
        data = message["data"]
        command = command.replace("$_", data)

    message['data'] = command # should this be allowed to alter the message? Maybe an action_data should be passed around too?