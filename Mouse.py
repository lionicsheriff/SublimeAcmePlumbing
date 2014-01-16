import sublime_plugin
from sublime import Region

class MouseCommand(sublime_plugin.TextCommand):
    """ Generic plugin for mouse handlers """

    def get_selection(self, mouseButton):
        """ Return a saved selection for a specified mouse button """
        settings = self.view.settings()
        key = "SublimePlumb-mouse" + mouseButton
        return settings.get(key, [])

    def save_selection(self, mouseButton, selection):
        """ Save a selection for the specified mouse button """
        settings = self.view.settings()
        key = "SublimePlumb-mouse" + mouseButton
        settings.set(key, selection)

    def remove_selection(self, mouseButton):
        """ Remove a saved selection """
        settings = self.view.settings()
        key = "SublimePlumb-mouse" + mouseButton
        settings.erase(key)

    def selection_at_cursor(self):
        """
        Return the selection at the cursor

        If the selection is more than one character it is directly used.

        Otherwise it is assumed you clicked and it goes through expansion rules:

            If it lands the selection made by the left mouse button, that
            is used.

            Otherwise the selection is expanded along the word boundaries
            using an agressive set of word separators

        The idea is that if you just click on a word you intended to select that
        word, this just saves some effort
        """

        selection = self.view.sel()[0]
        if selection.b - selection.a == 0:

            saved = [s for s in self.get_selection("1")
                        if s["a"] <= selection.a
                        and s["b"] >= selection.b]

            if len(saved) > 0:
                selection = Region(saved[0]["a"], saved[0]["b"])
            else:
                selection = self.expand_selection(selection)

        return selection


    def expand_selection (self, pos):
        settings = self.view.settings()
        old_boundaries = settings.get("word_separators")
        settings.set("word_separators"," ;,")
        expanded_selection = self.view.word(pos)
        settings.set("word_separators", old_boundaries)
        return expanded_selection
