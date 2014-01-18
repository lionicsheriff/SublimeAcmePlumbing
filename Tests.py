import os,re

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
    Extracts a jump command from the data. Jump commands have the same syntax as Go To Anything
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
    return (None,None)