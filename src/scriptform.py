#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main ScriptForm program
"""

import sys
import optparse
import os
import json
import logging
import threading
import hashlib
import socket

if hasattr(sys, 'dont_write_bytecode'):
    sys.dont_write_bytecode = True

# pylint: disable=wrong-import-position
from daemon import Daemon
from formdefinition import FormDefinition
from formconfig import FormConfig
from webserver import ThreadedHTTPServer
from webapp import ScriptFormWebApp


class ScriptForm(object):
    """
    'Main' class that orchestrates parsing the Form configurations and running
    the webserver.
    """
    def __init__(self, config_file, cache=True):
        self.config_file = config_file
        self.cache = cache
        self.log = logging.getLogger('SCRIPTFORM')
        self.form_config_singleton = None
        self.websrv = None
        self.running = False
        self.httpd = None

        # Init form config so it can raise errors about problems.
        self.get_form_config()

    def get_form_config(self):
        """
        Read and return the form configuration in the form of a FormConfig
        instance. If it has already been read, a cached version is returned.
        """
        # Cache
        if self.cache and self.form_config_singleton is not None:
            return self.form_config_singleton

        with open(self.config_file, "r") as fh:
            file_contents = fh.read()
        try:
            config = json.loads(file_contents)
        except ValueError as err:
            sys.stderr.write("Error in form configuration '{}': {}\n".format(
                self.config_file, err))
            sys.exit(1)

        static_dir = None
        custom_css = None
        users = None
        forms = []

        if 'static_dir' in config:
            static_dir = config['static_dir']
        if 'custom_css' in config:
            custom_css = file(config['custom_css'], 'r').read()
        if 'users' in config:
            users = config['users']
        for form in config['forms']:
            form_name = form['name']
            if not form['script'].startswith('/'):
                # Script is relative to the current dir
                script = os.path.join(os.path.realpath(os.curdir),
                                      form['script'])
            else:
                # Absolute path to the script
                script = form['script']
            forms.append(
                FormDefinition(form_name,
                               form['title'],
                               form['description'],
                               form.get('fields', None),
                               script,
                               fields_from=form.get("fields_from", None),
                               default_value=form.get('default_value', ""),
                               output=form.get('output', 'escaped'),
                               hidden=form.get('hidden', False),
                               submit_title=form.get('submit_title', 'Submit'),
                               allowed_users=form.get('allowed_users', None),
                               run_as=form.get('run_as', None))
            )

        form_config = FormConfig(
            config['title'],
            forms,
            users,
            static_dir,
            custom_css
        )
        self.form_config_singleton = form_config
        return form_config

    def run(self, listen_addr='0.0.0.0', listen_port=8081):
        """
        Start the webserver on address `listen_addr` and port `listen_port`.
        This call is blocking until the user hits Ctrl-c, the shutdown() method
        is called or something like SystemExit is raised in a handler.
        """
        ScriptFormWebApp.scriptform = self
        self.httpd = ThreadedHTTPServer((listen_addr, listen_port),
                                        ScriptFormWebApp)
        self.httpd.daemon_threads = True
        self.log.info("Listening on %s:%s", listen_addr, listen_port)
        self.running = True
        self.httpd.serve_forever()
        self.running = False

    def shutdown(self):
        """
        Shutdown the server. This interupts the run() method and must thus be
        run in a seperate thread.
        """
        self.log.info("Attempting server shutdown")

        def t_shutdown(scriptform_instance):
            """
            Callback for when the server is shutdown.
            """
            scriptform_instance.log.info(self.websrv)
            # Undocumented feature to shutdow the server.
            scriptform_instance.httpd.socket.close()
            scriptform_instance.httpd.shutdown()

        # We need to spawn a new thread in which the server is shut down,
        # because doing it from the main thread blocks, since the server is
        # waiting for connections..
        threading.Thread(target=t_shutdown, args=(1,))


def main():  # pragma: no cover
    """
    main method
    """
    usage = [
        sys.argv[0] + " [option] (--start|--stop) <form_definition.json>",
        "       " + sys.argv[0] + " --generate-pw",
    ]
    parser = optparse.OptionParser(version="%%VERSION%%")
    parser.set_usage('\n'.join(usage))

    parser.add_option("-g", "--generate-pw", dest="generate_pw",
                      action="store_true", default=False,
                      help="Generate password")
    parser.add_option("-p", "--port", dest="port", action="store", type="int",
                      default=8081, help="Port to listen on (default=8081)")
    parser.add_option("-f", "--foreground", dest="foreground",
                      action="store_true", default=False,
                      help="Run in foreground (debugging)")
    parser.add_option("-r", "--reload", dest="reload", action="store_true",
                      default=False,
                      help="Reload form config on every request (DEV)")
    parser.add_option("--pid-file", dest="pid_file", action="store",
                      default=None, help="Pid file")
    parser.add_option("--log-file", dest="log_file", action="store",
                      default=None, help="Log file")
    parser.add_option("--start", dest="action_start", action="store_true",
                      default=None, help="Start daemon")
    parser.add_option("--stop", dest="action_stop", action="store_true",
                      default=None, help="Stop daemon")

    (options, args) = parser.parse_args()

    if options.generate_pw:
        # Generate a password for use in the `users` section
        import getpass
        plain_pw = getpass.getpass()
        if plain_pw != getpass.getpass('Repeat password: '):
            sys.stderr.write("Passwords do not match.\n")
            sys.exit(1)
        sys.stdout.write(hashlib.sha256(plain_pw.encode('utf8')).hexdigest() + '\n')
        sys.exit(0)
    else:
        if not options.action_stop and len(args) < 1:
            parser.error("Insufficient number of arguments")
        if not options.action_stop and not options.action_start:
            options.action_start = True

        # If a form configuration was specified, change to that dir so we can
        # find the job scripts and such.
        if args:
            path = os.path.dirname(args[0])
            if path:
                os.chdir(path)
            args[0] = os.path.basename(args[0])

        daemon = Daemon(options.pid_file, options.log_file,
                        foreground=options.foreground)
        log = logging.getLogger('MAIN')
        try:
            if options.action_start:
                cache = not options.reload
                scriptform_instance = ScriptForm(args[0], cache=cache)
                daemon.register_shutdown_callback(scriptform_instance.shutdown)
                daemon.start()
                scriptform_instance.run(listen_port=options.port)
            elif options.action_stop:
                daemon.stop()
                sys.exit(0)
        except Exception as err:
            log.exception(err)
            raise


if __name__ == "__main__":  # pragma: no cover
    main()
