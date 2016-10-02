"""
The runscript module is responsible for running external scripts and processing
their output.
"""

import logging
import os
import pwd
import grp
import subprocess


log = logging.getLogger('RUNSCRIPT')


def run_as(uid, gid, groups):
    """Closure that changes the current running user and groups. Called before
    executing scripts by Subprocess."""
    def set_acc():
        """Change user and groups"""
        os.setgroups(groups)
        os.setgid(gid)
        os.setuid(uid)
    return set_acc


def run_script(form_def, form_values, stdout=None, stderr=None):
    """
    Perform a callback for the form `form_def`. This calls a script.
    `form_values` is a dictionary of validated values as returned by
    FormDefinition.validate(). If form_def.output is of type 'raw', `stdout`
    and `stderr` have to be open filehandles where the output of the
    callback should be written. The output of the script is hooked up to
    the output, depending on the output type.
    """
    # Validate params
    if form_def.output == 'raw' and (stdout is None or stderr is None):
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
        if form_def.run_as is not None:
            runas_pw = pwd.getpwnam(form_def.run_as)
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
        log.info("%s", (msg.format(runas_pw.pw_name,
                                   runas_gr.gr_name,
                                   str(groups))))
    else:
        run_as_fn = None
        if form_def.run_as is not None:
            log.critical("Not running as root, so we can't run the "
                         "script as user '%s'", (form_def.run_as))

    # If the form output type is 'raw', we directly stream the output to
    # the browser. Otherwise we store it for later displaying.
    if form_def.output == 'raw':
        try:
            proc = subprocess.Popen(form_def.script,
                                    shell=True,
                                    stdout=stdout,
                                    stderr=stderr,
                                    env=env,
                                    close_fds=True,
                                    preexec_fn=run_as_fn)
            stdout, stderr = proc.communicate(input)
            log.info("Exit code: %s", (proc.returncode))
            return proc.returncode
        except OSError as err:
            log.exception(err)
            stderr.write(str(err) + '. Please see the log file.')
            return -1
    else:
        try:
            proc = subprocess.Popen(form_def.script,
                                    shell=True,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    env=env,
                                    close_fds=True,
                                    preexec_fn=run_as_fn)
            stdout, stderr = proc.communicate()
            log.info("Exit code: %s", (proc.returncode))
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exitcode': proc.returncode
            }
        except OSError as err:
            log.exception(err)
            return {
                'stdout': '',
                'stderr': 'Internal error: {0}. Please see the log '
                          'file.'.format(str(err)),
                'exitcode': -1
            }
