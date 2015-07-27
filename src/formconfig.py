"""
FormConfig is the in-memory representation of a form configuration JSON file.
It holds information (title, users, the form definitions) on the form
configuration being served by this instance of ScriptForm.
"""

import logging
import stat
import os
import subprocess
import pwd
import grp


def run_as(uid, gid, groups):
    """Closure that changes the current running user and groups. Called before
    executing scripts by Subprocess."""
    def set_acc():
        """Change user and groups"""
        os.setgroups(groups)
        os.setgid(gid)
        os.setuid(uid)
    return set_acc


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

    def run_script(self, form_name, form_values, stdout=None, stderr=None):
        """
        Perform a callback for the form `form_name`. This calls a script.
        `form_values` is a dictionary of validated values as returned by
        FormDefinition.validate(). If form.output is of type 'raw', `stdout`
        and `stderr` have to be open filehandles where the output of the
        callback should be written. The output of the script is hooked up to
        the output, depending on the output type.
        """
        # FIXME: This doesn't really belong in FormCOnfig.
        form = self.get_form_def(form_name)

        # Validate params
        if form.output == 'raw' and (stdout is None or stderr is None):
            msg = 'stdout and stderr cannot be none if script output ' \
                  'is \'raw\''
            raise ValueError(msg)

        # Pass form values to the script through the environment as strings.
        env = os.environ.copy()
        for key, value in form_values.items():
            env[key] = str(value)

        # Get the user uid, gid and groups we should run as. If the current
        # user is root, we run as the given user or 'nobody' if no user was
        # specified. Otherwise, we run as the user we already are.
        if os.getuid() == 0:
            if form.run_as is not None:
                runas_pw = pwd.getpwnam(form.run_as)
            else:
                # Run as nobody
                runas_pw = pwd.getpwnam('nobody')
            runas_gr = grp.getgrgid(runas_pw.pw_gid)
            groups = [
                g.gr_gid
                for g in grp.getgrall()
                if runas_pw.pw_name in g.gr_mem
            ]
            msg = "Running script as user={0}, gid={1}, groups={2}"
            run_as_fn = run_as(runas_pw.pw_uid, runas_pw.pw_gid, groups)
            self.log.info(msg.format(runas_pw.pw_name, runas_gr.gr_name,
                                     str(groups)))
        else:
            run_as_fn = None
            if form.run_as is not None:
                self.log.critical("Not running as root, so we can't run the "
                                  "script as user '{0}'".format(form.run_as))

        # If the form output type is 'raw', we directly stream the output to
        # the browser. Otherwise we store it for later displaying.
        if form.output == 'raw':
            try:
                proc = subprocess.Popen(form.script, shell=True,
                                        stdout=stdout,
                                        stderr=stderr,
                                        env=env,
                                        close_fds=True,
                                        preexec_fn=run_as_fn)
                stdout, stderr = proc.communicate(input)
                self.log.info("Exit code: {0}".format(proc.returncode))
                return proc.returncode
            except OSError as err:
                self.log.exception(err)
                stderr.write(str(err) + '. Please see the log file.')
                return -1
        else:
            try:
                proc = subprocess.Popen(form.script, shell=True,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        env=env,
                                        close_fds=True,
                                        preexec_fn=run_as_fn)
                stdout, stderr = proc.communicate()
                self.log.info("Exit code: {0}".format(proc.returncode))
                return {
                    'stdout': stdout,
                    'stderr': stderr,
                    'exitcode': proc.returncode
                }
            except OSError as err:
                self.log.exception(err)
                return {
                    'stdout': '',
                    'stderr': 'Internal error: {0}. Please see the log '
                              'file.'.format(str(err)),
                    'exitcode': -1
                }
