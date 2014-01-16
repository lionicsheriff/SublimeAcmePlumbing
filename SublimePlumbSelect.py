from SublimePlumb.Mouse import MouseCommand

class SublimePlumbSaveSelection(MouseCommand):
    """ Save the last selection for each mouse button """
    def run_(self, edit_token, args):
        event = args['event']
        selection = [{"a": r.a, "b": r.b}
                     for r in self.view.sel()]
        self.save_selection(str(event["button"]), selection)