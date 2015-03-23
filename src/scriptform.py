#!/usr/bin/env python

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


def cmd(cmd, input=None, env=None):
    """
    Run command `cmd` in a shell. `input` (string) is passed in the
    process' STDIN.

    Returns a dictionary: `{'stdout': <string>, 'stderr': <string>, 'exitcode':
    <int>}`.
    """
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env)
    stdout, stderr = p.communicate(input)
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
    def __init__(self, name, title, description, fields, script=None,
                 submit_title="Submit"):
        self.name = name
        self.title = title
        self.description = description
        self.fields = fields
        self.script = script
        self.submit_title = submit_title

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
            if field_name == 'form_name':
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
                    "Required field {} not present".format(field['name']))

        return values

    def validate_field(self, field_name, value):
        """
        Validate a field in this form.
        """
        # Find field definition by iterating through all the fields.
        field_def = self.get_field(field_name)
        if not field_def:
            raise KeyError("Unknown field: {}".format(field_name))

        field_type = field_def['type']
        validate_cb = getattr(self, 'validate_{}'.format(field_type), None)
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
            #g = m.groups()
            #return datetime.date(int(g[0]), int(g[1]), int(g[2]))
        elif field_def.get('required', False):
            raise ValueError(
                "Invalid value for date field: {}".format(value))
        return None

    def validate_radio(self, field_def, value):
        if not value in [o[0] for o in field_def['options']]:
            raise ValueError(
                "Invalid value for radio button: {}".format(value))
        return value

    def validate_select(self, field_def, value):
        if not value in [o[0] for o in field_def['options']]:
            raise ValueError(
                "Invalid value for dropdown: {}".format(value))
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
        """
        response_code = 200
        method_name = 'h_{}'.format(path)
        try:
            if hasattr(self, method_name) and \
               callable(getattr(self, method_name)):
                out = getattr(self, method_name)(**params)
            elif path == '' and hasattr(self, 'index'):
                out = self.index(**params)
            elif hasattr(self, 'default'):
                out = self.default(**params)
            else:
                response_code = 404
                out = 'Not Found'
        except Exception, e:
            self.wfile.write(e)
            raise
        self.send_response(response_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(out)


class ScriptFormWebApp(WebAppHandler):
    """
    This class is a request handler for WebSrv.
    """
    def index(self):
        return self.h_list()

    def h_list(self):
        h_form_list = []
        for form_name, form_def in self.vitaform.forms.items():
            h_form_list.append('''
              <li>
                <h2 class="form-title">{title}</h2>
                <p class="form-description">{description}</p>
                <a class="form-link btn" href="/form?form_name={name}">
                  {title}
                </a>
              </li>
            '''.format(title=form_def.title,
                       description=form_def.description,
                       name=form_name)
            )

        return '''
          {header}
          <div class="list">
            {form_list}
          </div>
          {footer}
        '''.format(header=html_header.format(title=self.vitaform.title),
                   footer=html_footer,
                   form_list=''.join(h_form_list))

    def h_form(self, form_name):
        field_tpl = {
            "string": '<input {} type="text" name="{}" />',
            "number": '<input {} type="number" min="{}" max="{}" name="{}" />',
            "integer": '<input {} type="number" min="{}" max="{}" name="{}" />',
            "float": '<input {} type="number" min="{}" max="{}" name="{}" />',
            "date": '<input {} type="date" name="{}" />',
            "file": '<input {} type="file" name="{}" />',
            "password": '<input {} type="password" name="{}" />',
            "text": '<textarea {} name="{}"></textarea>',
            "select": '<option value="{}">{}</option>',
            "radio": '<input checked type="radio" name="{}" value="{}">{}<br/>',
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
                input = '<select {} name="{}">{}</select>'.format(required, field['name'], options)
            else:
                raise ValueError("Unsupported field type: {}".format(
                    field['type'])
                )

            return ('''
              <li>
                <p class="form-field-title">{title}</p>
                <p class="form-field-input">{input}</p>
              </li>
            '''.format(title=field['title'],
                       input=input))

        form = self.vitaform.get_form(form_name)

        return '''
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
            header=html_header.format(title=self.vitaform.title),
            footer=html_footer,
            title=form.title,
            description=form.description,
            name=form.name,
            fields=''.join([render_field(f) for f in form.fields]),
            submit_title=form.submit_title
        )

    def h_submit(self, form_values):
        form_name = form_values.getfirst('form_name', None)

        # Validate the form values
        form = self.vitaform.get_form(form_name)
        values = form.validate(form_values)

        # Call user's callback
        if form.script:
            # Run an external script
            env = os.environ.copy()
            env.update(values)
            res = cmd(form.script, env=env)
            if res['exitcode'] != 0:
                result = '<span class="error">{}</span>'.format(res['stderr'])
            else:
                result = '<pre>{}</pre>'.format(res['stdout'])
        else:
            # Run a python callback
            callback = self.callbacks[form_name]
            result = callback(values)

        return '''
            {header}
            <div class="result">
              <h2 class="result-title">{title}</h2>
              <h3 class="result-subtitle">Result</h3>
              <div class="result-result">{result}</div>
              <ul class="nav">
                <li>
                  <a class="back-list btn" href="/">Back to the list</a>
                </li>
                <li>
                  <a class="back-form btn" href="/form?form_name={form_name}">
                    Back to the form
                  </a>
                </li>
              </ul>
            </div>
            {footer}
        '''.format(
            header=html_header.format(title=self.vitaform.title),
            footer=html_footer,
            title=form.title,
            form_name=form.name,
            result=result,
        )


class ScriptForm:
    """
    'Main' class that orchestrates parsing the Form definition file
    `config_file`, hooking up callbacks and running the webserver.
    """
    def __init__(self, config_file, callbacks={}):
        self.forms = {}
        self.callbacks = {}
        self.title = 'ScriptForm Actions'
        self.basepath = os.path.realpath(os.path.dirname(config_file))

        self._load_config(config_file)
        for form_name, cb in callbacks.items():
            self.callbacks[form_name] = cb

        # Validate scripts
        for form_name, form_def in self.forms.items():
            if form_def.script:
                if not stat.S_IXUSR & os.stat(form_def.script)[stat.ST_MODE]:
                    raise Exception("{} is not executable".format(form_def.script))
            else:
                if not form_name in self.callbacks:
                    raise Exception("No script or callback registered for '{}'".format(form_name))

    def _load_config(self, path):
        config = json.load(file(path, 'r'))
        if 'title' in config:
            self.title = config['title']
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
                               submit_title=form.get('submit_title', None))

    def get_form(self, form_name):
        return self.forms[form_name]

    def run(self, listen_addr='0.0.0.0', listen_port=80):
        ScriptFormWebApp.vitaform = self
        ScriptFormWebApp.callbacks = self.callbacks
        #webapp = ScriptFormWebApp(vitaform, self.callbacks)
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
