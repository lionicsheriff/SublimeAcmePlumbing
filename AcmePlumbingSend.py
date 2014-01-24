import sublime, sublime_plugin
import os
from .Mouse import MouseCommand

class AcmePlumbingSend(MouseCommand):
    """ Sends the current selected text to the plumbing """
    def run(self, edit):
        file_name = self.view.file_name()
        message = {
            "data": self.view.substr(self.selection_at_cursor()),
            "cwd": os.path.dirname(file_name) if file_name else None,
            "src": self.view.id(),
        }
        self.remove_selection("1") # in case it was expanded
        self.view.sel().clear()
        self.view.run_command("acme_plumbing", message)
