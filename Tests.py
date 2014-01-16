import os,re

def is_file(message, args):
    """ Tests if the data in the message is a file, and returns the full path """
    file = message.get("data", None)
    if file:
        if os.path.isfile(file):
            return file
        else:
            cwd = message["cwd"]
            relative_path = os.path.normpath(cwd + '/' + file)
            if os.path.isfile(relative_path):
                return relative_path
    return None

def pattern(message, pattern):
    """ Tests the message data against a regex pattern """
    text = message.get("data", None)
    if text != None:
        return re.search(pattern, text)
    return None
