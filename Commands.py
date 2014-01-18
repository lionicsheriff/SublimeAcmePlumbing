import sublime, os, re
from sublime import Region
from subprocess import Popen, PIPE

def is_file(message, args, pipeline_data):
    """ Tests if the data in the message is a file, and returns the full path """
    file = message.get("data", None)
    if file:
        cwd = message["cwd"]
        if os.path.isfile(file):
            return file
        elif cwd:
            relative_path = os.path.normpath(cwd + '/' + file)
            if os.path.isfile(relative_path):
                return relative_path
    return None

def is_dir(message, args, pipeline_data):
    """ Tests if the data in the message is a directory, and returns the full path """
    file = message.get("data", None)
    if file:
        cwd = message["cwd"] # hmm, may need something better than getting the cwd off the file name if I want to chain the out put of ls/dir (since they are transient files, they don't have a cwd)
        if os.path.isdir(file):
            return file
        elif cwd:
            relative_path = os.path.normpath(cwd + '/' + file)
            if os.path.isfile(relative_path):
                return relative_path
    return None

def pattern(message, args, pipeline_data):
    """ Tests the message data against a regex pattern """
    text = message.get("data", None)
    pattern = args[0]
    if text != None:
        return re.search(pattern, text)
    return None

def extract_jump(message, args, pipeline_data):
    """ 
    Extracts a jump command from the data, and proceeds to the next step.
    Jump commands have the same syntax as Go To Anything
    e.g.:
        @ to jump to a symbol
        : to jump to a line
        # to jump to an instance of the text

    NOTE: the jump command is removed from the data. This is useful for subsequent tests like
          is_file, as otherwise the jump command will cause it to fail

    Returns a tuple containing (type, location)
    """

    text = message.get("data", None)
    if text != None:
        match = re.search("([@#:])([^@#:]+?)$", text)
        if match:
            message['data'] = text[0:match.span(1)[0]]
            return (match.group(1), match.group(2))
    return (None,None) # this will be considered as true

def open_in_tab(message, args, pipeline_data):
    """ Opens a file, or output of a command in a new tab """
    cwd = message['cwd']
    command = message['data']
    window = sublime.active_window()
    if os.path.isfile(command):
        tab = window.open_file(command)
        return tab
    else:
        p = Popen([command], shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if out:
            data = out.decode(encoding='utf-8')
            tab = window.new_file()
            tab.set_scratch(True)
            edit_token = message['edit_token']
            tab.insert(edit_token, 0, data)
            return tab

def open_in_external_program(message, args, pipeline_data):
    """ Starts an external program to view the message data """
    cwd = message['cwd']
    command = message['data']
    return Popen([command], shell=True, cwd=cwd, close_fds=True)

def prepare_command(message, args, pipeline_data):
    """ Munges the message data based off results of earlier match data """
    command = args[0]

    # replace group place holders
    # unnamed groups replace $groupnumber with the result
    #   e.g. $1
    # named groups use $groupname
    #   e.g. $file_name
    if "pattern" in pipeline_data:
        match = pipeline_data["pattern"]
        for idx, val in enumerate(match.groups()):
            group = idx + 1 # 0 is the full matched text
            command = command.replace("$" + str(group), val)

        for group,val in match.groupdict().items():
            command = command.replace("$" + group, val)

    # $_ is either the related file, or the original data
    if "is_file" in pipeline_data:
        file_name = pipeline_data["is_file"]
        command = command.replace("$_", file_name)
    elif "data" in message:
        data = message["data"]
        command = command.replace("$_", data)

    message['data'] = command # should this be allowed to alter the message? Maybe an action_data should be passed around too?
    return command



def jump(message, args, pipeline_data):
    jump_type, jump_location = pipeline_data.get("extract_jump")
    window = sublime.active_window()
    view = window.active_view()

    location = 0
    if jump_type == "@":
        # jump to symbol
        for result in window.lookup_symbol_in_open_files(jump_location):
            view_file = view.file_name()
            result_file = result[0]

            # annoyingly the result format is different than the file name in windows                     
            if os.name == 'nt':
                if not result_file.startswith("//"):
                    # unc paths start with // and they probably only need normalisation
                    # we need to turn /C/a_file.txt into C:\a_file.txt

                    # drop the leading /
                    result_file = result_file[1:]

                     # inject : into the second characte (NOTE: it is :\ 'cause the string is growing)
                    result_file = result_file[:1] + ":\\" + result_file[2:]

                # regardless, we need to flip the slashes
                result_file = os.path.normpath(result_file)

            if view_file == result_file:
                location = view.text_point(result[2][0] - 1, result[2][1] - 1)
                break
        pass
    elif jump_type == "#":
        # jump to search result

        # get the current position, so you can search forwards if the
        # jump is called on the same page
        sel = view.sel() 
        current_pos = view.sel()[0] if len(sel) > 0 else sublime.Region(0,0)
        next_pos = view.find(jump_location,current_pos.b + 1) # test pass the cursor so it can find the next instance

        # wrap around if nothing is found
        if next_pos.a == -1:
            next_pos = view.find(jump_location,1)

        # hopefully we have found something by now
        if next_pos.a != -1:
            location = next_pos.a

    elif jump_type == ":":
        location = view.text_point(int(jump_location) - 1, 0)

    view.sel().clear()
    view.sel().add(Region(location))
    view.show(location)
    return location
