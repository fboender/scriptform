"""
The webapp part of Scriptform, which takes care of serving requests and
handling them.
"""

from SocketServer import ThreadingMixIn
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import cgi
import logging
import tempfile
import os
import base64
import hashlib

from formrender import FormRender


HTML_HEADER = u'''<html>
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
    div.form li.hidden {{ display: none; }}
    div.form p.form-field-title {{ margin-bottom: 0px; }}
    div.form p.form-field-input {{ margin-top: 0px; }}
    div.form li.checkbox p.form-field-input {{ float: left;
                                               margin-right: 8px; }}
    div.form li.required abbr {{ color: #FF0000; }}
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

    /* Custom css */
    {custom_css}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="page">
'''

HTML_FOOTER = u'''
    <div class="about">
      Powered by
      <a href="https://github.com/fboender/scriptform">Scriptform</a>
      v%%VERSION%%
    </div>
  </div>
</body>
</html>
'''

HTML_LIST = u''''
{header}
<div class="list">
  {form_list}
</div>
{footer}
'''

HTML_FORM = u'''
{header}
<div class="form">
  <h2 class="form-title">{title}</h2>
  <p class="form-description">{description}</p>
  <form id="{name}" action="submit" method="post"
   enctype="multipart/form-data">
    <input type="hidden" name="form_name" value="{name}" />
    <ul>
        {fields}
        <li class="submit">
          <input type="submit" class="btn btn-act" value="{submit_title}" />
          <a href=".">
            <button type="button" class="btn btn-lnk" value="Back">
              Back to the list
            </button>
          </a>
        </li>
    </ul>
  </form>
</div>
{footer}
'''

HTML_FORM_LIST = u'''
  <li>
    <h2 class="form-title">{title}</h2>
    <p class="form-description">{description}</p>
    <a class="form-link btn btn-act" href="./form?form_name={name}">
      {title}
    </a>
  </li>
'''

HTML_SUBMIT_RESPONSE = u'''
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


class HTTPError(Exception):
    """
    HTTPError may be thrown by routes to indicate HTTP errors such as 404, 301,
    etc. They are caught by the 'framework' and sent to the client's browser.
    """
    def __init__(self, status_code, msg, headers=None):
        if headers is None:
            headers = {}
        self.status_code = status_code
        self.msg = msg
        self.headers = headers
        Exception.__init__(self, status_code, msg, headers)


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """
    Base class for multithreaded HTTP servers.
    """
    pass


class WebAppHandler(BaseHTTPRequestHandler):
    """
    Basic web server request handler. Handles GET and POST requests. This class
    should be extended with methods (starting with 'h_') to handle the actual
    requests. If no path is set, it dispatches to the 'index' or 'default'
    method.
    """
    def log_message(self, fmt, *args):
        """Overrides BaseHTTPRequestHandler which logs to the console. We log
        to our log file instead"""
        fmt = "{} {}"
        self.scriptform.log.info(fmt.format(self.address_string(), args))

    def do_GET(self):
        """
        Handle a GET request.
        """
        self._call(*self._parse(self.path))

    def do_POST(self):
        """
        Handle a POST request.
        """
        form_values = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'})
        self._call(self.path.strip('/'), params={'form_values': form_values})

    def _parse(self, reqinfo):
        """
        Parse information from a request.
        """
        url_comp = urlparse.urlsplit(reqinfo)
        path = url_comp.path
        query_vars = urlparse.parse_qs(url_comp.query)
        # Only return the first value of each query var. E.g. for
        # "?foo=1&foo=2" return '1'.
        var_values = dict([(k, v[0]) for k, v in query_vars.items()])
        return (path.strip('/'), var_values)

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
                method_cb = getattr(self, 'index')
            elif hasattr(self, 'default'):
                method_cb = getattr(self, 'default')
            else:
                raise HTTPError(404, "Not found")
            method_cb(**params)
        except HTTPError, err:
            # HTTP erors are generally thrown by the webapp on purpose. Send
            # error to the browser.
            if err.status_code not in (401, ):
                self.scriptform.log.exception(err)
            self.send_response(err.status_code)
            for header_k, header_v in err.headers.items():
                self.send_header(header_k, header_v)
            self.end_headers()
            self.wfile.write("Error {}: {}".format(err.status_code,
                                                   err.msg))
            self.wfile.flush()
            return False
        except Exception, err:
            self.scriptform.log.exception(err)
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

        username = getattr(self, 'username', None)
        visible_forms = form_config.get_visible_forms(username)
        if len(visible_forms) == 1:
            first_form = visible_forms[0]
            return self.h_form(first_form.name)
        else:
            return self.h_list()

    def auth(self):
        """
        Verify that the user is authenticated. This is required if the form
        definition contains a 'users' field. Returns the username if the user
        is validated or None if no validation is required.. Otherwise, raises a
        401 HTTP back to the client.
        """
        form_config = self.scriptform.get_form_config()
        username = None

        # If a 'users' element was present in the form configuration file, the
        # user must be authenticated.
        if form_config.users:
            auth_header = self.headers.getheader("Authorization")
            if auth_header is not None:
                # Validate the username and password
                auth_unpw = auth_header.split(' ', 1)[1]
                username, password = base64.decodestring(auth_unpw).split(":")
                pw_hash = hashlib.sha256(password).hexdigest()

                if username in form_config.users and \
                   pw_hash == form_config.users[username]:
                    # Valid username and password. Return the username.
                    return username

            # Authentication needed, but not provided or wrong username/pw.
            headers = {"WWW-Authenticate": 'Basic realm="Private Area"'}
            raise HTTPError(401, 'Authenticate', headers)

        # No authentication required. Return None as the username.
        return None

    def h_list(self):
        """
        Render a list of available forms.
        """
        username = self.auth()

        form_config = self.scriptform.get_form_config()
        h_form_list = []
        for form_def in form_config.get_visible_forms(username):
            h_form_list.append(
                HTML_FORM_LIST.format(
                    title=form_def.title,
                    description=form_def.description,
                    name=form_def.name
                )
            )

        output = HTML_LIST.format(
            header=HTML_HEADER.format(title=form_config.title,
                                      custom_css=form_config.custom_css),
            footer=HTML_FOOTER,
            form_list=u''.join(h_form_list)
        )
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(output.encode('utf8'))

    def h_form(self, form_name, errors=None, **form_values):
        """
        Render a form.
        """
        def render_field(field, errors):
            """
            Render a HTML field.
            """
            params = {
                'name': field['name'],
                'classes': [],
            }

            if field.get('hidden', None):
                params['classes'].append('hidden')

            if field.get('required', None):
                params['classes'].append('required')

            params['classes'].extend(field.get('classes', '').split())

            params["style"] = field.get("style", "")

            # Get field-specific parameters
            if field['type'] not in ('file', 'checkbox'):
                params['value'] = form_values.get(field['name'], '')

            if field['type'] not in ('radio', 'checkbox', 'select'):
                params['required'] = field.get('required', False)

            if field['type'] == 'string':
                params['size'] = field.get('size', '')

            if field['type'] in ('string', 'password', 'text'):
                params['minlen'] = field.get('minlen', '')

            if field['type'] in ('string', 'text'):
                params['maxlen'] = field.get('maxlen', '')

            if field['type'] in ('integer', 'float'):
                params['minval'] = field.get("min", '')
                params['maxval'] = field.get("max", '')

            if field['type'] == 'date':
                params['minval'] = field.get('min', '')
                params['maxval'] = field.get('max', '')

            if field['type'] == 'text':
                params['rows'] = field.get("rows", '')
                params['cols'] = field.get("cols", '')

            if field['type'] == 'radio':
                if not form_values.get(field['name'], None):
                    params['value'] = field['options'][0][0]
                params['options'] = field['options']

            if field['type'] in ('radio', 'select'):
                params['options'] = field['options']

            if field['type'] == 'checkbox':
                params['checked'] = False
                if field['name'] in form_values and \
                   form_values[field['name']] == 'on':
                    params['checked'] = True

            h_input = fr_inst.r_field(field['type'], **params)

            return fr_inst.r_form_line(field['type'], field['title'],
                                       h_input, params['classes'], errors)

        if errors is None:
            errors = {}

        username = self.auth()

        form_config = self.scriptform.get_form_config()
        fr_inst = FormRender(None)

        # Make sure the user is allowed to access this form.
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           username not in form_def.allowed_users:
            raise HTTPError(403, "You're not authorized to view this form")

        html_errors = u''
        if errors:
            html_errors = u'<ul>'
            for error in errors:
                html_errors += u'<li class="error">{0}</li>'.format(error)
            html_errors += u'</ul>'

        output = HTML_FORM.format(
            header=HTML_HEADER.format(title=form_config.title,
                                      custom_css=form_config.custom_css),
            footer=HTML_FOOTER,
            title=form_def.title,
            description=form_def.description,
            errors=html_errors,
            name=form_def.name,
            fields=u''.join(
                [render_field(f, errors.get(f['name'], []))
                 for f in form_def.fields]
            ),
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
        username = self.auth()

        form_config = self.scriptform.get_form_config()
        form_name = form_values.getfirst('form_name', None)
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           username not in form_def.allowed_users:
            raise HTTPError(403, "You're not authorized to view this form")

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
            if field.filename is not None:
                # Field is an uploaded file. Stream it to a temp file if
                # something was actually uploaded
                if field.filename == '':
                    continue
                tmp_fname = tempfile.mktemp(prefix="scriptform_")
                tmp_file = file(tmp_fname, 'w')
                while True:
                    buf = field.file.read(1024 * 16)
                    if not buf:
                        break
                    tmp_file.write(buf)
                tmp_file.close()
                field.file.close()

                tmp_files.append(tmp_fname)  # For later cleanup
                values[field_name] = tmp_fname
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

            # Log the callback and its parameters for auditing purposes.
            log = logging.getLogger('CALLBACK_AUDIT')
            cwd = os.path.realpath(os.curdir)
            log.info("Calling script: {0}".format(form_def.script))
            log.info("Current working dir: {0}".format(cwd))
            log.info("User: {0}".format(username))
            log.info("Variables: {0}".format(dict(form_values.items())))

            result = form_config.callback(form_name, form_values, self.wfile,
                                          self.wfile)
            if form_def.output != 'raw':
                # Ignore everything if we're doing raw output, since it's the
                # scripts responsibility.
                if result['exitcode'] != 0:
                    stderr = cgi.escape(result['stderr'].decode('utf8'))
                    msg = u'<span class="error">{0}</span>'.format(stderr)
                else:
                    if form_def.output == 'escaped':
                        stdout = cgi.escape(result['stdout'].decode('utf8'))
                        msg = u'<pre>{0}</pre>'.format(stdout)
                    else:
                        # Non-escaped output (html, usually)
                        msg = result['stdout'].decode('utf8')

                output = HTML_SUBMIT_RESPONSE.format(
                    header=HTML_HEADER.format(
                        title=form_config.title,
                        custom_css=form_config.custom_css
                    ),
                    footer=HTML_FOOTER,
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
            form_values.pop('form_name')
            self.h_form(form_name, form_errors, **form_values)

        # Clean up uploaded files
        for file_name in tmp_files:
            if os.path.exists(file_name):
                os.unlink(file_name)

    def h_static(self, fname):
        """Serve static files"""
        self.auth()

        form_config = self.scriptform.get_form_config()

        if not form_config.static_dir:
            raise HTTPError(501, "Static file serving not enabled")

        if '..' in fname:
            raise HTTPError(403, "Invalid file name")

        path = os.path.join(form_config.static_dir, fname)
        if not os.path.exists(path):
            raise HTTPError(404, "Not found")

        static_file = file(path, 'r')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(static_file.read())
