#!/usr/bin/env python

# Todo:
#
#  - file uploads should be saved to temp files and passed to the callback.
#  - Ignore non-existing temp files in upload cleanup.
#  - How does script_raw check the exitcode? Document this.
#  - Validate field values properly.
#     * Integer/float min, max
#     * Uploaded files mime-types/extensions

import sys
import optparse
import os
import stat
import json
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import cgi
import re
import datetime
import subprocess
import base64
import tempfile


html_header = '''<html>
<head>
  <style>
    .btn {{ color: #FFFFFF; font-weight: bold; font-size: 0.90em;
           background-color: #1D98E4; border-color: #1D98E4; padding: 9px;
           border-radius: 4px; border-width: 0px; text-decoration: none;
           }}
    .error {{ color: #FF0000; }}
    *,body {{ font-family: sans-serif; }}
    h1 {{ color: #555555; text-align: center; margin: 32px auto 32px auto; }}
    pre {{ font-family: monospace; }}

    /* List of available forms */
    div.list {{ width: 50%; margin: 40px auto 0px auto; }}
    div.list li {{ font-size: 0.90em; list-style: none;
                  margin-bottom: 65px; }}
    div.list h2 {{ background-color: #E0E5E5;
                  border-radius: 3px; font-weight: bold;
                  padding: 10px; font-size: 1.2em; }}
    div.list p.form-description {{ margin-left: 25px; }}
    div.list a.form-link {{ margin-left: 25px; }}

    /* Form display */
    div.form {{ width: 50%; margin: 40px auto 0px auto; }}
    div.form h2 {{ font-weight: bold; background-color: #E0E5E5; padding: 25px;
                  border-radius: 10px; }}
    div.form p.form-description {{ font-size: 0.90em;
                                  margin: 40px 25px 65px 25px; }}
    div.form li {{ font-size: 0.90em; list-style: none; }}
    div.form p.form-field-title {{ margin-bottom: 0px; }}
    div.form p.form-field-input {{ margin-top: 0px; }}
    select,
    textarea,
    input[type=text],
    input[type=number],
    input[type=date],
    input[type=password],
    input[type=submit] {{ color: #606060; padding: 9px; border-radius: 4px;
                         border: 1px solid #D0D0D0;
                         background-color: #F9F9F9;}}
    input[type=submit] {{ color: #FFFFFF; font-weight: bold;
                         background-color: #1D98E4; border-color: #1D98E4}}
    textarea {{ width: 80%; height: 120px; }}
    /* Result display */
    div.result {{ width: 50%; margin: 40px auto 0px auto; }}
    div.result h2 {{ background-color: #E0E5E5; border-radius: 3px;
                    font-weight: bold; padding: 10px; }}
    div.result div.result-result {{ margin-left: 25px; }}
    div.result ul {{ margin-top: 64px; padding-left: 0px; }}
    div.result ul li {{ list-style: none; float: left; margin-right: 20px;
                        font-size: 0.90em; }}
    div.result ul.nav {{ margin-bottom: 128px; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="page">
'''

html_footer = '''
  </div>
</body>
</html>
'''


class FormDefinition:
    """
    FormDefinition holds information about a single form and provides methods
    for validation of the form values.
    """
    def __init__(self, name, title, description, fields, script=None,
                 script_raw=False, submit_title="Submit",
                 allowed_users=None):
        self.name = name
        self.title = title
        self.description = description
        self.fields = fields
        self.script = script
        self.script_raw = script_raw
        self.submit_title = submit_title
        self.allowed_users = allowed_users

    def get_field(self, field_name):
        for field in self.fields:
            if field['name'] == field_name:
                return field

    def validate(self, form_values):
        """
        Validate all relevant fields for this form against form_values.
        """
        values = {}
        for field_name in form_values:
            if field_name == 'form_name' or \
               form_values[field_name].filename:
                continue
            v = self.validate_field(field_name,
                                    form_values.getfirst(field_name))
            if v is not None:
                values[field_name] = v

        # Make sure all required fields are there
        for field in self.fields:
            if 'required' in field and \
               field['required'] is True and \
               field['name'] not in values:
                raise ValueError(
                    "Required field {0} not present".format(field['name']))

        return values

    def validate_field(self, field_name, value):
        """
        Validate a field in this form.
        """
        # Find field definition by iterating through all the fields.
        field_def = self.get_field(field_name)
        if not field_def:
            raise KeyError("Unknown field: {0}".format(field_name))

        field_type = field_def['type']
        validate_cb = getattr(self, 'validate_{0}'.format(field_type), None)
        if not validate_cb:
            return value
        else:
            return validate_cb(field_def, value)

    def validate_integer(self, field_def, value):
        try:
            int(value)
            return value
        except ValueError:
            if field_def.get('required', False):
                raise
        return None

    def validate_float(self, field_def, value):
        try:
            return float(value)
        except ValueError:
            if field_def.get('required', False):
                raise
        return None

    def validate_date(self, field_def, value):
        m = re.match('([0-9]{4})-([0-9]{2})-([0-9]{2})', value)
        if m:
            return value
        elif field_def.get('required', False):
            raise ValueError(
                "Invalid value for date field: {0}".format(value))
        return None

    def validate_radio(self, field_def, value):
        if not value in [o[0] for o in field_def['options']]:
            raise ValueError(
                "Invalid value for radio button: {0}".format(value))
        return value

    def validate_select(self, field_def, value):
        if not value in [o[0] for o in field_def['options']]:
            raise ValueError(
                "Invalid value for dropdown: {0}".format(value))
        return value


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


class WebSrv:
    """
    Very basic web server.
    """
    def __init__(self, request_handler, listen_addr='', listen_port=80):
        httpd = ThreadedHTTPServer((listen_addr, listen_port), request_handler)
        httpd.serve_forever()


class WebAppHandler(BaseHTTPRequestHandler):
    """
    Basic web server request handler. Handles GET and POST requests. This class
    should be extended with methods (starting with 'h_') to handle the actual
    requests. If no path is set, it dispatches to the 'index' or 'default'
    method.
    """
    def do_GET(self):
        self.call(*self.parse(self.path))

    def do_POST(self):
        form_values = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'})
        self.call(self.path.strip('/'), params={'form_values': form_values})

    def parse(self, reqinfo):
        if '?' in reqinfo:
            path, params = reqinfo.split('?', 1)
            params = dict(
                [p.split('=', 1) for p in params.split('&') if '=' in p]
            )
            return (path.strip('/'), params)
        else:
            return (self.path.strip('/'), {})

    def call(self, path, params):
        """
        Find a method to call on self.app_class based on `path` and call it.
        The method that's called is in the form 'h_<PATH>'. If no path was
        given, it will try to call the 'index' method. If no method could be
        found but a `default` method exists, it is called. Otherwise 404 is
        sent.

        Methods should take care of sending proper headers and content
        themselves using self.send_response(), self.send_header(),
        self.end_header() and by writing to self.wfile.
        """
        method_name = 'h_{0}'.format(path)
        method_cb = None
        try:
            if hasattr(self, method_name) and \
               callable(getattr(self, method_name)):
                method_cb = getattr(self, method_name)
            elif path == '' and hasattr(self, 'index'):
                method_cb = self.index
            elif hasattr(self, 'default'):
                method_cb = self.default
            else:
                self.send_error(404, "Not found")
                return
            method_cb(**params)
        except Exception, e:
            self.send_error(500, "Internal server error")
            raise


class ScriptFormWebApp(WebAppHandler):
    """
    This class is a request handler for WebSrv.
    """
    def index(self):
        return self.h_list()

    def auth(self):
        """
        Verify that the user is authenticated. This is required if the form
        definition contains a 'users' field. Returns True if the user is
        validated. Otherwise, returns False and sends 401 HTTP back to the
        client.
        """
        self.username = None

        # If a 'users' element was present in the form configuration file, the
        # user must be authenticated.
        if self.scriptform.users:
            authorized = False
            auth_header = self.headers.getheader("Authorization")
            if auth_header is not None:
                auth_realm, auth_unpw = auth_header.split(' ', 1)
                username, password = base64.decodestring(auth_unpw).split(":")
                # Validate the username and password
                if username in self.scriptform.users and \
                   password == self.scriptform.users[username]:
                    self.username = username
                    authorized = True

            if not authorized:
                # User is not authenticated. Send authentication request.
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="Private Area"')
                self.end_headers()
                return False
        return True

    def h_list(self):
        if not self.auth():
            return

        h_form_list = []
        for form_name, form_def in self.scriptform.forms.items():
            if form_def.allowed_users is not None and \
               self.username not in form_def.allowed_users:
                continue # User is not allowed to run this form
            h_form_list.append('''
              <li>
                <h2 class="form-title">{title}</h2>
                <p class="form-description">{description}</p>
                <a class="form-link btn" href="./form?form_name={name}">
                  {title}
                </a>
              </li>
            '''.format(title=form_def.title,
                       description=form_def.description,
                       name=form_name)
            )

        output = '''
          {header}
          <div class="list">
            {form_list}
          </div>
          {footer}
        '''.format(header=html_header.format(title=self.scriptform.title),
                   footer=html_footer,
                   form_list=''.join(h_form_list))
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        #self.send_header('Expires', 'Mon, 30 Mar 2015 16:00:00 GMT')
        self.end_headers()
        self.wfile.write(output)

    def h_form(self, form_name):
        if not self.auth():
            return

        field_tpl = {
            "string": '<input {0} type="text" name="{1}" />',
            "number": '<input {0} type="number" min="{1}" max="{2}" name="{3}" />',
            "integer": '<input {0} type="number" min="{1}" max="{2}" name="{3}" />',
            "float": '<input {0} type="number" min="{1}" max="{2}" name="{3}" />',
            "date": '<input {0} type="date" name="{1}" />',
            "file": '<input {0} type="file" name="{1}" />',
            "password": '<input {0} type="password" name="{1}" />',
            "text": '<textarea {0} name="{1}"></textarea>',
            "select": '<option value="{0}">{1}</option>',
            "radio": '<input checked type="radio" name="{0}" value="{1}">{2}<br/>',
        }

        def render_field(field):
            tpl = field_tpl[field['type']]

            required = ''
            if field.get('required', None):
                required='required'

            if field['type'] == 'string':
                input = tpl.format(required, field['name'])
            elif field['type'] == 'number' or \
                    field['type'] == 'integer' or \
                    field['type'] == 'float':
                input = tpl.format(required, field.get('min', ''),
                                   field.get('max', ''),
                                   field['name'])
            elif field['type'] == 'date':
                input = tpl.format(required, field['name'])
            elif field['type'] == 'file':
                input = tpl.format(required, field['name'])
            elif field['type'] == 'password':
                input = tpl.format(required, field['name'])
            elif field['type'] == 'radio':
                input = ''.join(
                    [
                        tpl.format(field['name'], o[0], o[1])
                        for o in field['options']
                    ]
                )
            elif field['type'] == 'text':
                input = tpl.format(required, field['name'])
            elif field['type'] == 'select':
                options = ''.join([
                        tpl.format(o[0], o[1]) for o in field['options']
                    ]
                )
                input = '<select {0} name="{1}">{2}</select>'.format(required, field['name'], options)
            else:
                raise ValueError("Unsupported field type: {0}".format(
                    field['type'])
                )

            return ('''
              <li>
                <p class="form-field-title">{title}</p>
                <p class="form-field-input">{input}</p>
              </li>
            '''.format(title=field['title'],
                       input=input))

        form_def = self.scriptform.get_form(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            raise Exception("Not authorized")

        output = '''
          {header}
          <div class="form">
            <h2 class="form-title">{title}</h2>
            <p class="form-description">{description}</p>
            <form action="submit" method="post" enctype="multipart/form-data">
              <input type="hidden" name="form_name" value="{name}" />
              <ul>
                  {fields}
                  <li><input type="submit" value="{submit_title}" /></li>
              </ul>
            </form>
          </div>
          {footer}
        '''.format(
            header=html_header.format(title=self.scriptform.title),
            footer=html_footer,
            title=form_def.title,
            description=form_def.description,
            name=form_def.name,
            fields=''.join([render_field(f) for f in form_def.fields]),
            submit_title=form_def.submit_title
        )
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        #self.send_header('Expires', 'Mon, 30 Mar 2015 16:00:00 GMT')
        self.end_headers()
        self.wfile.write(output)

    def h_submit(self, form_values):
        if not self.auth():
            return

        form_name = form_values.getfirst('form_name', None)
        form_def = self.scriptform.get_form(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            raise Exception("Not authorized")

        # Write contents of all uploaded files to temp files. These temp
        # filenames are passed to the callbacks instead of the actual contents.
        file_fields = {}
        for field_name in form_values:
            field = form_values[field_name]
            if field.filename:
                tmpfile = tempfile.mktemp(prefix="scriptform_")
                f = file(tmpfile, 'w')
                while True:
                    buf = field.file.read(1024 * 16)
                    if not buf:
                        break
                    f.write(buf)
                f.close()
                field.file.close()
                file_fields[field_name] = tmpfile

        # Validate the form values
        form_values = form_def.validate(form_values)

        # Repopulate form values with uploaded tmp filenames
        form_values.update(file_fields)

        # Call user's callback. If a result is returned, we assume the callback
        # was not a raw script, so we wrap its output in some nice HTML.
        # Otherwise the callback should have written its own response to the
        # self.wfile filehandle.
        try:
            result = self.scriptform.callback(form_name, form_values, self.wfile)
            if result:
                if result['exitcode'] != 0:
                    msg = '<span class="error">{0}</span>'.format(result['stderr'])
                else:
                    msg = '<pre>{0}</pre>'.format(result['stdout'])
                output = '''
                    {header}
                    <div class="result">
                      <h2 class="result-title">{title}</h2>
                      <h3 class="result-subtitle">Result</h3>
                      <div class="result-result">{msg}</div>
                      <ul class="nav">
                        <li>
                          <a class="back-list btn" href=".">Back to the list</a>
                        </li>
                        <li>
                          <a class="back-form btn" href="form?form_name={form_name}">
                            Back to the form
                          </a>
                        </li>
                      </ul>
                    </div>
                    {footer}
                '''.format(
                    header=html_header.format(title=self.scriptform.title),
                    footer=html_footer,
                    title=form_def.title,
                    form_name=form_def.name,
                    msg=msg,
                )
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                #self.send_header('Expires', 'Mon, 30 Mar 2015 16:00:00 GMT')
                self.end_headers()
                self.wfile.write(output)
        finally:
            # Clean up uploaded files
            # FIXME: Catch exceptions and such)
            for file_name in file_fields.values():
                os.unlink(file_name)

class ScriptForm:
    """
    'Main' class that orchestrates parsing the Form definition file
    `config_file`, hooking up callbacks and running the webserver.
    """
    def __init__(self, config_file, callbacks={}):
        self.forms = {}
        self.callbacks = {}
        self.title = 'ScriptForm Actions'
        self.users = None
        self.basepath = os.path.realpath(os.path.dirname(config_file))

        self._load_config(config_file)
        for form_name, cb in callbacks.items():
            self.callbacks[form_name] = cb

        # Validate scripts
        for form_name, form_def in self.forms.items():
            if form_def.script:
                if not stat.S_IXUSR & os.stat(form_def.script)[stat.ST_MODE]:
                    raise Exception("{0} is not executable".format(form_def.script))
            else:
                if not form_name in self.callbacks:
                    raise Exception("No script or callback registered for '{0}'".format(form_name))

    def _load_config(self, path):
        config = json.load(file(path, 'r'))
        if 'title' in config:
            self.title = config['title']
        if 'users' in config:
            self.users = config['users']
        for form_name, form in config['forms'].items():
            if 'script' in form:
                script = os.path.join(self.basepath, form['script'])
            else:
                script = None
            self.forms[form_name] = \
                FormDefinition(form_name,
                               form['title'],
                               form['description'],
                               form['fields'],
                               script,
                               script_raw=form.get('script_raw', False),
                               submit_title=form.get('submit_title', None),
                               allowed_users=form.get('allowed_users', None))

    def get_form(self, form_name):
        return self.forms[form_name]

    def callback(self, form_name, form_values, output_fh=None):
        form = self.get_form(form_name)
        if form.script:
            return self.callback_script(form, form_values, output_fh)
        else:
            return self.callback_python(form, form_values, output_fh)

    def callback_script(self, form, form_values, output_fh=None):
        env = os.environ.copy()
        env.update(form_values)

        if form.script_raw:
            p = subprocess.Popen(form.script, shell=True, stdout=output_fh,
                                 stderr=output_fh, env=env)
            stdout, stderr = p.communicate(input)
            return None
        else:
            p = subprocess.Popen(form.script, shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=env)
            stdout, stderr = p.communicate()
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exitcode': p.returncode
            }

    def callback_python(self, form, form_values, output_fh=None):
        pass

    def run(self, listen_addr='0.0.0.0', listen_port=80):
        ScriptFormWebApp.scriptform = self
        ScriptFormWebApp.callbacks = self.callbacks
        WebSrv(ScriptFormWebApp, listen_addr=listen_addr, listen_port=listen_port)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.set_usage(sys.argv[0] + " [option] <form_definition.json>")

    parser.add_option("-p", "--port", dest="port", action="store", type="int", default=80, help="Port to listen on.")

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("Insufficient number of arguments")

    sf = ScriptForm(args[0])
    sf.run(listen_port=options.port)
