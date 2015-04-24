#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Todo:
#
#  - How does script_raw check the exitcode? Document this.
#  - Default values for input fields.
#  - If there are errors in the form, its values are empties.
#  - Send responses using self.send_ if possible
#  - Maintain order of forms in form configuration.

import sys
import optparse
import os
import stat
import json
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import cgi
import datetime
import subprocess
import base64
import tempfile
import hashlib
import urlparse
import atexit
import signal
import time
import errno
import logging


html_header = u'''<html>
<head>
  <meta charset="UTF-8">
  <style>
    /* Default classes */
    .btn {{ color: #FFFFFF; font-weight: bold; font-size: 0.9em;
            background-color: #1D98E4; padding: 9px; border-radius: 4px;
            border-width: 0px; text-decoration: none; }}
    .btn-act {{ background-color: #1D98E4; }}
    .btn-lnk {{ background-color: #D0D0D0; }}
    .error {{ color: #FF0000; }}

    /* Main element markup */
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
    input[type=password] {{ color: #606060; padding: 9px; border-radius: 4px;
                            border: 1px solid #D0D0D0;
                            background-color: #F9F9F9; }}
    textarea {{ font-family: monospace; }}

    /* Result display */
    div.result {{ width: 50%; margin: 40px auto 0px auto; }}
    div.result h2 {{ background-color: #E0E5E5; border-radius: 3px;
                    font-weight: bold; padding: 10px; }}
    div.result div.result-result {{ margin-left: 25px; }}
    div.result ul.nav {{ margin: 64px 0px 128px 0px; padding-left: 0px; }}
    div.result ul.nav li {{ list-style: none; float: left;
                        font-size: 0.90em; margin-right: 20px; }}

    /* Other */
    div.about {{ text-align: center; font-size: 12px; color: #808080; }}
    div.about a {{ text-decoration: none; color: #000000; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="page">
'''

html_footer = u'''
  <div class="about">Powered by <a href="https://github.com/fboender/scriptform">Scriptform</a></div>
  </div>
</body>
</html>
'''

html_list = u''''
{header}
<div class="list">
  {form_list}
</div>
{footer}
'''

html_form = u'''
{header}
<div class="form">
  <h2 class="form-title">{title}</h2>
  <p class="form-description">{description}</p>
  <form action="submit" method="post" enctype="multipart/form-data">
    <input type="hidden" name="form_name" value="{name}" />
    <ul>
        {fields}
        <li>
          <input type="submit" class="btn btn-act" value="{submit_title}" />
          <a href="."><button type="button" class="btn btn-lnk" value="Back">Back to the list</button></a>
        </li>
    </ul>
  </form>
</div>
{footer}
'''

html_submit_response = u'''
{header}
<div class="result">
  <h2 class="result-title">{title}</h2>
  <h3 class="result-subtitle">Result</h3>
  <div class="result-result">{msg}</div>
  <ul class="nav">
    <li>
      <a class="back-form btn btn-lnk" href="form?form_name={form_name}">
        Back to the form
      </a>
    </li>
    <li><a class="btn btn-lnk" href=".">Back to the list</a></li>
  </ul>
</div>
{footer}
'''


class ValidationError(Exception):
    pass


class ScriptFormError(Exception):
    pass


class DaemonError(Exception):
    pass


class ScriptForm:
    """
    'Main' class that orchestrates parsing the Form configurations and running
    the webserver.
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.basepath = os.path.realpath(os.path.dirname(config_file))
        self.log = logging.getLogger('SCRIPTFORM')
        self.get_form_config()  # Init form config so it can raise errors about problems.
        self.websrv = None

    def get_form_config(self):
        """
        Read and return the form configuration in the form of a FormConfig
        instance. If it has already been read, a cached version is returned.
        """
        # Cache
        if hasattr(self, 'form_config_singleton'):
            return self.form_config_singleton

        path = self.config_file
        config = json.load(file(path, 'r'))

        forms = []
        users = None

        if 'users' in config:
            users = config['users']
        for form in config['forms']:
            form_name = form['name']
            script = os.path.join(self.basepath, form['script'])
            forms.append(
                FormDefinition(form_name,
                               form['title'],
                               form['description'],
                               form['fields'],
                               script,
                               output=form.get('output', 'escaped'),
                               submit_title=form.get('submit_title', 'Submit'),
                               allowed_users=form.get('allowed_users', None))
            )

        form_config = FormConfig(
            config['title'],
            forms,
            users
        )
        self.form_config_singleton = form_config
        return form_config

    def run(self, listen_addr='0.0.0.0', listen_port=80):
        """
        Start the webserver on address `listen_addr` and port `listen_port`.
        This call is blocking and will never return unless the user hits
        Ctrl-c.
        """
        ScriptFormWebApp.scriptform = self
        self.httpd = ThreadedHTTPServer((listen_addr, listen_port), ScriptFormWebApp)
        self.log.info("Listening on {0}:{1}".format(listen_addr, listen_port))
        self.httpd.serve_forever()

    def shutdown(self):
        self.log.info("Attempting server shutdown")
        self.log.info(self.websrv)
        # FIXME: This is not the cleanest way to exit. shutdown() is called by
        # the atexit and signal handler. Ideally, we should call
        # self.httpd.shutdown(), but that doesn't work because we're in the
        # same thread.
        raise SystemExit()


class FormConfig:
    """
    FormConfig is the in-memory representation of a form configuration JSON
    file. It holds information (title, users, the form definitions) on the
    form configuration being served by this instance of ScriptForm.
    """
    def __init__(self, title, forms, users={}):
        self.title = title
        self.users = users
        self.forms = forms

        # Validate scripts
        for form_def in self.forms:
            if not stat.S_IXUSR & os.stat(form_def.script)[stat.ST_MODE]:
                raise ScriptFormError("{0} is not executable".format(form_def.script))

    def get_form_def(self, form_name):
        """
        Return the form definition for the form with name `form_name`. Returns
        an instance of FormDefinition class or raises ValueError if the form
        was not found.
        """
        for form_def in self.forms:
            if form_def.name == form_name:
                return form_def
        else:
            raise ValueError("No such form: {0}".format(form_name))

    def callback(self, form_name, form_values, request):
        """
        Perform a callback for the form `form_name`. This calls a script.
        `form_values` is a dictionary of validated values as returned by
        FormDefinition.validate(). `request` is the request handler context
        (ScriptFormWebApp). The output of the script is hooked up to the
        output, depending on the output type.
        """
        form = self.get_form_def(form_name)

        os.chdir(os.path.dirname(form.script))

        # Pass form values to the script through the environment as strings.
        env = os.environ.copy()
        for k, v in form_values.items():
            env[k] = str(v)

        if form.output == 'raw':
            p = subprocess.Popen(form.script, shell=True,
                                 stdout=request.wfile,
                                 stderr=request.wfile,
                                 env=env)
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


class FormDefinition:
    """
    FormDefinition holds information about a single form and provides methods
    for validation of the form values.
    """
    def __init__(self, name, title, description, fields, script,
                 output='escaped', submit_title="Submit",
                 allowed_users=None):
        self.name = name
        self.title = title
        self.description = description
        self.fields = fields
        self.script = script
        self.output = output
        self.submit_title = submit_title
        self.allowed_users = allowed_users

    def _get_field(self, field_name):
        for field in self.fields:
            if field['name'] == field_name:
                return field

    def validate(self, form_values):
        """
        Validate all relevant fields for this form against form_values.
        """
        errors = {}
        values = form_values.copy()

        # First make sure all required fields are there
        for field in self.fields:
            if 'required' in field and \
               field['required'] is True and \
               field['name'] not in form_values:
                errors.setdefault(field['name'], []).append(
                    "This field is required"
                )

        # Validate the field values, possible casting them to the correct type.
        for field in self.fields:
            field_name = field['name']
            if field_name == 'form_name':
                continue
            try:
                v = self._field_validate(field_name, form_values)
                if v is not None:
                    values[field_name] = v
            except ValidationError, e:
                errors.setdefault(field_name, []).append(str(e))

        return (errors, values)

    def _field_validate(self, field_name, form_values):
        """
        Validate a field in this form. This does a dynamic call to a method on
        this class in the form 'validate_<field_type>'.
        """
        # Find field definition by iterating through all the fields.
        field_def = self._get_field(field_name)
        if not field_def:
            raise ValidationError("Unknown field: {0}".format(field_name))

        field_type = field_def['type']
        validate_cb = getattr(self, 'validate_{0}'.format(field_type), None)
        return validate_cb(field_def, form_values)

    def validate_string(self, field_def, form_values):
        value = form_values[field_def['name']]
        maxlen = field_def.get('maxlen', None)
        minlen = field_def.get('minlen', None)

        if minlen is not None and len(value) < minlen:
            raise ValidationError("Minimum length is {0}".format(minlen))
        if maxlen is not None and len(value) > maxlen:
            raise ValidationError("Maximum length is {0}".format(maxlen))

        return value

    def validate_integer(self, field_def, form_values):
        value = form_values[field_def['name']]
        max = field_def.get('max', None)
        min = field_def.get('min', None)

        try:
            value = int(value)
        except ValueError:
            raise ValidationError("Must be an integer number")

        if min is not None and value < min:
            raise ValidationError("Minimum value is {0}".format(min))
        if max is not None and value > max:
            raise ValidationError("Maximum value is {0}".format(max))

        return int(value)

    def validate_float(self, field_def, form_values):
        value = form_values[field_def['name']]
        max = field_def.get('max', None)
        min = field_def.get('min', None)

        try:
            value = float(value)
        except ValueError:
            raise ValidationError("Must be an real (float) number")

        if min is not None and value < min:
            raise ValidationError("Minimum value is {0}".format(min))
        if max is not None and value > max:
            raise ValidationError("Maximum value is {0}".format(max))

        return float(value)

    def validate_date(self, field_def, form_values):
        value = form_values[field_def['name']]
        max = field_def.get('max', None)
        min = field_def.get('min', None)

        try:
            value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid date, must be in form YYYY-MM-DD")

        if min is not None:
            if value < datetime.datetime.strptime(min, '%Y-%m-%d').date():
                raise ValidationError("Minimum value is {0}".format(min))
        if max is not None:
            if value > datetime.datetime.strptime(max, '%Y-%m-%d').date():
                raise ValidationError("maximum value is {0}".format(max))

        return value

    def validate_radio(self, field_def, form_values):
        value = form_values[field_def['name']]
        if not value in [o[0] for o in field_def['options']]:
            raise ValidationError(
                "Invalid value for radio button: {0}".format(value))
        return value

    def validate_select(self, field_def, form_values):
        value = form_values[field_def['name']]
        if not value in [o[0] for o in field_def['options']]:
            raise ValidationError(
                "Invalid value for dropdown: {0}".format(value))
        return value

    def validate_text(self, field_def, form_values):
        value = form_values[field_def['name']]
        minlen = field_def.get('minlen', None)
        maxlen = field_def.get('maxlen', None)

        if minlen is not None:
            if len(value) < minlen:
                raise ValidationError("minimum length is {0}".format(minlen))

        if maxlen is not None:
            if len(value) > maxlen:
                raise ValidationError("maximum length is {0}".format(maxlen))

        return value

    def validate_password(self, field_def, form_values):
        value = form_values[field_def['name']]
        minlen = field_def.get('minlen', None)

        if minlen is not None:
            if len(value) < minlen:
                raise ValidationError("minimum length is {0}".format(minlen))

        return value

    def validate_file(self, field_def, form_values):
        value = form_values[field_def['name']]
        field_name = field_def['name']
        upload_fname = form_values[u'{0}__name'.format(field_name)]
        upload_fname_ext = os.path.splitext(upload_fname)[-1].lstrip('.')
        extensions = field_def.get('extensions', None)

        if extensions is not None and upload_fname_ext not in extensions:
            raise ValidationError("Only file types allowed: {0}".format(u','.join(extensions)))

        return value


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


class WebAppHandler(BaseHTTPRequestHandler):
    """
    Basic web server request handler. Handles GET and POST requests. This class
    should be extended with methods (starting with 'h_') to handle the actual
    requests. If no path is set, it dispatches to the 'index' or 'default'
    method.
    """
    def do_GET(self):
        self._call(*self._parse(self.path))

    def do_POST(self):
        form_values = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'})
        self._call(self.path.strip('/'), params={'form_values': form_values})

    def _parse(self, reqinfo):
        url_comp = urlparse.urlsplit(reqinfo)
        path = url_comp.path
        qs = urlparse.parse_qs(url_comp.query)
        # Only return the first value of each query var. E.g. for
        # "?foo=1&foo=2" return '1'.
        vars = dict([(k, v[0]) for k, v in qs.items()])
        return (path.strip('/'), vars)

    def _call(self, path, params):
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
            self.scriptform.log.exception(e)
            self.send_error(500, "Internal server error")
            raise


class ScriptFormWebApp(WebAppHandler):
    """
    This class is a request handler for WebSrv.
    """
    def index(self):
        """
        Index handler. If there's only one form defined, render that form.
        Otherwise render a list of available forms.
        """
        form_config = self.scriptform.get_form_config()
        if len(form_config.forms) == 1:
            first_form = form_config.forms[0]
            return self.h_form(first_form.name)
        else:
            return self.h_list()

    def auth(self):
        """
        Verify that the user is authenticated. This is required if the form
        definition contains a 'users' field. Returns True if the user is
        validated. Otherwise, returns False and sends 401 HTTP back to the
        client.
        """
        form_config = self.scriptform.get_form_config()
        self.username = None

        # If a 'users' element was present in the form configuration file, the
        # user must be authenticated.
        if form_config.users:
            authorized = False
            auth_header = self.headers.getheader("Authorization")
            if auth_header is not None:
                auth_realm, auth_unpw = auth_header.split(' ', 1)
                username, password = base64.decodestring(auth_unpw).split(":")
                pw_hash = hashlib.sha256(password).hexdigest()
                # Validate the username and password
                if username in form_config.users and \
                   pw_hash == form_config.users[username]:
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
        """
        Render a list of available forms.
        """
        form_config = self.scriptform.get_form_config()
        if not self.auth():
            return

        h_form_list = []
        for form_def in form_config.forms:
            if form_def.allowed_users is not None and \
               self.username not in form_def.allowed_users:
                continue  # User is not allowed to run this form
            h_form_list.append(u'''
              <li>
                <h2 class="form-title">{title}</h2>
                <p class="form-description">{description}</p>
                <a class="form-link btn btn-act" href="./form?form_name={name}">
                  {title}
                </a>
              </li>
            '''.format(title=form_def.title,
                       description=form_def.description,
                       name=form_def.name)
            )

        output = html_list.format(
            header=html_header.format(title=form_config.title),
            footer=html_footer,
            form_list=u''.join(h_form_list)
        )
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(output.encode('utf8'))

    def h_form(self, form_name, errors={}):
        """
        Render a form.
        """
        form_config = self.scriptform.get_form_config()
        if not self.auth():
            return

        field_tpl = {
            "string": u'<input {0} type="text" name="{1}" />',
            "number": u'<input {0} type="number" min="{1}" max="{2}" name="{3}" />',
            "integer": u'<input {0} type="number" min="{1}" max="{2}" name="{3}" />',
            "float": u'<input {0} type="number" min="{1}" max="{2}" step="any" name="{3}" />',
            "date": u'<input {0} type="date" name="{1}" />',
            "file": u'<input {0} type="file" name="{1}" />',
            "password": u'<input {0} type="password" min="{1}" name="{2}" />',
            "text": u'<textarea {0} name="{1}" rows="{2}" cols="{3}"></textarea>',
            "select": u'<option value="{0}">{1}</option>',
            "radio": u'<input {0} type="radio" name="{1}" value="{2}">{3}<br/>',
        }

        def render_field(field, errors):
            tpl = field_tpl[field['type']]

            required = u''
            if field.get('required', None):
                required = 'required'

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
                input = tpl.format(required, field.get('minlen', ''), field['name'])
            elif field['type'] == 'radio':
                radio_elems = []
                checked = u'checked'
                for option in field['options']:
                    radio_elems.append(tpl.format(checked, field['name'], option[0], option[1]))
                    checked = u''  # Check first radio option
                input = u''.join(radio_elems)
            elif field['type'] == 'text':
                rows = field.get('rows', 5)
                cols = field.get('cols', 80)
                input = tpl.format(
                    required,
                    field['name'],
                    rows,
                    cols
                )
            elif field['type'] == 'select':
                options = u''.join([tpl.format(o[0], o[1]) for o in field['options']])
                input = u'<select {0} name="{1}">{2}</select>'.format(required, field['name'], options)
            else:
                raise ValueError("Unsupported field type: {0}".format(
                    field['type'])
                )

            return (u'''
              <li>
                <p class="form-field-title">{title}</p>
                <p class="form-field-input">{input} <span class="error">{errors}</span></p>
              </li>
            '''.format(title=field['title'],
                       input=input,
                       errors=u', '.join(errors)))

        # Make sure the user is allowed to access this form.
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            self.send_error(401, "You're not authorized to view this form")
            return

        html_errors = u''
        if errors:
            html_errors = u'<ul>'
            for error in errors:
                html_errors += u'<li class="error">{0}</li>'.format(error)
            html_errors += u'</ul>'

        output = html_form.format(
            header=html_header.format(title=form_config.title),
            footer=html_footer,
            title=form_def.title,
            description=form_def.description,
            errors=html_errors,
            name=form_def.name,
            fields=u''.join([render_field(f, errors.get(f['name'], [])) for f in form_def.fields]),
            submit_title=form_def.submit_title
        )
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(output.encode('utf8'))

    def h_submit(self, form_values):
        """
        Handle the submitting of a form by validating the values and then doing
        a callback to a script. How the output is
        handled depends on settings in the form definition.
        """
        form_config = self.scriptform.get_form_config()
        if not self.auth():
            return

        form_name = form_values.getfirst('form_name', None)
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            self.send_error(401, "You're not authorized to view this form")
            return

        # Convert FieldStorage to a simple dict, because we're not allowd to
        # add items to it. For normal fields, the form field name becomes the
        # key and the value becomes the field value. For file upload fields, we
        # stream the uploaded file to a temp file and then put the temp file in
        # the destination dict. We also add an extra field with the originally
        # uploaded file's name.
        values = {}
        tmp_files = []
        for field_name in form_values:
            field = form_values[field_name]
            if field.filename:
                # Field is an uploaded file. Stream it to a temp file
                tmpfile = tempfile.mktemp(prefix="scriptform_")
                f = file(tmpfile, 'w')
                while True:
                    buf = field.file.read(1024 * 16)
                    if not buf:
                        break
                    f.write(buf)
                f.close()
                field.file.close()

                tmp_files.append(tmpfile)  # For later cleanup
                values[field_name] = tmpfile
                values['{0}__name'.format(field_name)] = field.filename
            else:
                # Field is a normal form field. Store its value.
                values[field_name] = form_values.getfirst(field_name, None)

        # Validate the form values
        form_errors, form_values = form_def.validate(values)

        if not form_errors:
            # Call user's callback. If a result is returned, we wrap its output
            # in some nice HTML. If no result is returned, the output was raw
            # and the callback should have written its own response to the
            # self.wfile filehandle.
            result = form_config.callback(form_name, form_values, self)
            if result:
                if result['exitcode'] != 0:
                    msg = u'<span class="error">{0}</span>'.format(cgi.escape(result['stderr'].decode('utf8')))
                else:
                    if form_def.output == 'escaped':
                        msg = u'<pre>{0}</pre>'.format(cgi.escape(result['stdout'].decode('utf8')))
                    else:
                        msg = result['stdout'].decode('utf8')

                output = html_submit_response.format(
                    header=html_header.format(title=form_config.title),
                    footer=html_footer,
                    title=form_def.title,
                    form_name=form_def.name,
                    msg=msg,
                )
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(output.encode('utf8'))
        else:
            # Form had errors
            self.h_form(form_name, form_errors)

        # Clean up uploaded files
        for file_name in tmp_files:
            if os.path.exists(file_name):
                os.unlink(file_name)


class Daemon:
    """
    Daemonize the current process (detach it from the console).
    """
    def __init__(self, pid_file, log_file=None, log_level=logging.INFO, foreground=False):
        if pid_file is None:
            self.pid_file = '{0}.pid'.format(os.path.basename(sys.argv[0]))
        else:
            self.pid_file = pid_file
        if log_file is None:
            self.log_file = '{0}.log'.format(os.path.basename(sys.argv[0]))
        else:
            self.log_file = log_file
        self.foreground = foreground

        logging.basicConfig(level=log_level,
                            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                            filename=self.log_file,
                            filemode='a')
        self.log = logging.getLogger('DAEMON')
        self.shutdown_cb = None

    def register_shutdown_cb(self, cb):
        self.shutdown_cb = cb

    def start(self):
        self.log.info("Starting")
        if self.is_running():
            self.log.error('Already running')
            raise DaemonError("Already running")
        if not self.foreground:
            self._fork()

    def stop(self):
        if not self.is_running():
            raise DaemonError("Not running")

        pid = self.get_pid()

        # Kill the daemon and wait until the process is gone
        os.kill(pid, signal.SIGTERM)
        for timeout in range(25):  # 5 seconds
            time.sleep(0.2)
            if not self._pid_running(pid):
                break
        else:
            self.log.error("Couldn't stop the daemon.")

    def is_running(self):
        """
        Check if the daemon is already running by looking at the PID file
        """
        if self.get_pid() is None:
            return False
        else:
            return True

    def get_pid(self):
        """
        Returns the PID of this daemon. If the daemon is not running (the PID
        file does not exist or the PID in the PID file does not exist), returns
        None.
        """
        if not os.path.exists(self.pid_file):
            return None

        try:
            pid = int(file(self.pid_file, 'r').read().strip())
        except ValueError:
            return None

        if os.path.isdir('/proc/{0}/'.format(pid)):
            return pid
        else:
            os.unlink(self.pid_file)
        return None

    def _pid_running(self, pid):
        """
        Returns True if the PID is running, False otherwise
        """
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return False
        return True

    def _fork(self):
        # Fork a child and end the parent (detach from parent)
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # End parent

        # Change some defaults so the daemon doesn't tie up dirs, etc.
        os.setsid()
        os.umask(0)

        # Fork a child and end parent (so init now owns process)
        pid = os.fork()
        if pid > 0:
            self.log.info("PID = {0}".format(pid))
            f = file(self.pid_file, 'w')
            f.write(str(pid))
            f.close()
            sys.exit(0)  # End parent

        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._cleanup)

        # Close STDIN, STDOUT and STDERR so we don't tie up the controlling
        # terminal
        for fd in (0, 1, 2):
            try:
                os.close(fd)
            except OSError:
                pass

        # Reopen the closed file descriptors so other os.open() calls don't
        # accidentally get tied to the stdin etc.
        os.open("/dev/null", os.O_RDWR)  # standard input (0)
        os.dup2(0, 1)                    # standard output (1)
        os.dup2(0, 2)                    # standard error (2)

        return pid

    def _cleanup(self, signal=None, frame=None):
        self.log.info("Received signal {0}".format(signal))
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)
        self.shutdown_cb()


if __name__ == "__main__":
    usage = [
        sys.argv[0] + " [option] (--start|--stop) <form_definition.json>",
        "       " + sys.argv[0] + " --generate-pw",
    ]
    parser = optparse.OptionParser(version="%%VERSION%%")
    parser.set_usage('\n'.join(usage))

    parser.add_option("-g", "--generate-pw", dest="generate_pw", action="store_true", default=False, help="Generate password")
    parser.add_option("-p", "--port", dest="port", action="store", type="int", default=80, help="Port to listen on")
    parser.add_option("-f", "--foreground", dest="foreground", action="store_true", default=False, help="Run in foreground (debugging)")
    parser.add_option("--pid-file", dest="pid_file", action="store", default=None, help="Pid file")
    parser.add_option("--log-file", dest="log_file", action="store", default=None, help="Log file")
    parser.add_option("--start", dest="action_start", action="store_true", default=None, help="Start daemon")
    parser.add_option("--stop", dest="action_stop", action="store_true", default=None, help="Stop daemon")

    (options, args) = parser.parse_args()

    if options.generate_pw:
        # Generate a password for use in the `users` section
        import getpass
        plain_pw = getpass.getpass()
        if not plain_pw == getpass.getpass('Repeat password: '):
            sys.stderr.write("Passwords do not match.\n")
            sys.exit(1)
        print hashlib.sha256(plain_pw).hexdigest()
        sys.exit(0)
    else:
        if not options.action_stop and len(args) < 1:
            parser.error("Insufficient number of arguments")
        if not options.action_stop and not options.action_start:
            options.action_start = True
        daemon = Daemon(options.pid_file, options.log_file, foreground=options.foreground)
        log = logging.getLogger('MAIN')
        try:
            if options.action_start:
                sf = ScriptForm(args[0])
                daemon.register_shutdown_cb(sf.shutdown)
                daemon.start()
                sf.run(listen_port=options.port)
            elif options.action_stop:
                daemon.stop()
                sys.exit(0)
        except Exception, e:
            log.exception(e)
            raise
