"""
FormConfig is the in-memory representation of a form configuration JSON file.
It holds information (title, users, the form definitions) on the form
configuration being served by this instance of ScriptForm.
"""

import logging
import stat
import os


class FormConfigError(Exception):
    """
    Default error for FormConfig errors
    """
    pass


class FormConfig(object):
    """
    FormConfig is the in-memory representation of a form configuration JSON
    file. It holds information (title, users, the form definitions) on the
    form configuration being served by this instance of ScriptForm.
    """
    def __init__(self, title, forms, users=None, static_dir=None,
                 custom_css=None):
        self.title = title
        self.users = {}
        if users is not None:
            self.users = users
        self.forms = forms
        self.static_dir = static_dir
        self.custom_css = custom_css
        self.log = logging.getLogger('FORMCONFIG')

        # Validate scripts
        for form_def in self.forms:
            if not stat.S_IXUSR & os.stat(form_def.script)[stat.ST_MODE]:
                msg = "{0} is not executable".format(form_def.script)
                raise FormConfigError(msg)

    def get_form_def(self, form_name):
        """
        Return the form definition for the form with name `form_name`. Returns
        an instance of FormDefinition class or raises ValueError if the form
        was not found.
        """
        for form_def in self.forms:
            if form_def.name == form_name:
                return form_def

        raise ValueError("No such form: {0}".format(form_name))

    def get_visible_forms(self, username=None):
        """
        Return a list of all visible forms. Excluded forms are those that have
        the 'hidden' property set, and where the user has no access to.
        """
        form_list = []
        for form_def in self.forms:
            if form_def.allowed_users is not None and \
               username not in form_def.allowed_users:
                continue  # User is not allowed to run this form
            if form_def.hidden:
                continue  # Don't show hidden forms in the list.
            else:
                form_list.append(form_def)
        return form_list
