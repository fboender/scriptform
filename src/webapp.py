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
    div.form li.hidden {{ display: none; }}
    div.form p.form-field-title {{ margin-bottom: 0px; }}
    div.form p.form-field-input {{ margin-top: 0px; }}
    div.form li.checkbox p.form-field-input {{ float: left; margin-right: 8px; }}
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

html_footer = u'''
  <div class="about">Powered by <a href="https://github.com/fboender/scriptform">Scriptform</a> v%%VERSION%%</div>
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
  <form id="{name}" action="submit" method="post" enctype="multipart/form-data">
    <input type="hidden" name="form_name" value="{name}" />
    <ul>
        {fields}
        <li class="submit">
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


class HTTPError(Exception):
    def __init__(self, status_code, msg, headers=None):
        if headers is None:
            headers = {}
        self.status_code = status_code
        self.msg = msg
        self.headers = headers
        Exception.__init__(self, status_code, msg, headers)


class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
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
        var_values = dict([(k, v[0]) for k, v in qs.items()])
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
                # FIXME: Raise Error
                self.send_error(404, "Not found")
                return
            method_cb(**params)
        except HTTPError, e:
            if e.status_code not in (401, ):
                self.scriptform.log.exception(e)
            self.send_response(e.status_code)
            for header_k, header_v in e.headers.items():
                self.send_header(header_k, header_v)
            self.end_headers()
            return False
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

        visible_forms = form_config.get_visible_forms(getattr(self, 'username', None))
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
        self.username = None

        # If a 'users' element was present in the form configuration file, the
        # user must be authenticated.
        if form_config.users:
            authorized = False
            auth_header = self.headers.getheader("Authorization")
            if auth_header is not None:
                auth_unpw = auth_header.split(' ', 1)[1]
                username, password = base64.decodestring(auth_unpw).split(":")
                pw_hash = hashlib.sha256(password).hexdigest()
                # Validate the username and password
                if username in form_config.users and \
                   pw_hash == form_config.users[username]:
                    self.username = username
                    authorized = True

            if not authorized:
                headers = {
                    "WWW-Authenticate": 'Basic realm="Private Area"'
                }
                raise HTTPError(401, 'Authenticate', headers)
        return True

    def h_list(self):
        """
        Render a list of available forms.
        """
        if not self.auth():
            return

        form_config = self.scriptform.get_form_config()
        h_form_list = []
        for form_def in form_config.get_visible_forms(getattr(self, 'username', None)):
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
            header=html_header.format(title=form_config.title,
                                      custom_css=form_config.custom_css),
            footer=html_footer,
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
        if errors is None:
            errors = {}
        if not self.auth():
            return

        form_config = self.scriptform.get_form_config()
        fr = FormRender(None)

        def render_field(field, errors):
            params = {
                'name': field['name'],
                'classes': [],
            }

            if field.get('hidden', None):
                params['classes'].append('hidden')

            params["style"] = field.get("style", "")

            if field['type'] not in ('file', 'checkbox'):
                params['value'] = form_values.get(field['name'], '')

            if field['type'] not in ('radio', 'checkbox', 'select'):
                params['required'] = field.get('required', False)

            if field['type'] in ('string'):
                params['size'] = field.get('size', '')

            if field['type'] in ('number', 'integer', 'float', 'password'):
                params['minval'] = field.get("min", '')

            if field['type'] in ('number', 'integer', 'float'):
                params['maxval'] = field.get("max", '')

            if field['type'] in ('text'):
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
                if field['name'] in form_values and form_values[field['name']] == 'on':
                    params['checked'] = True

            h_input = fr.r_field(field['type'], **params)

            return fr.r_form_line(field['type'], field['title'],
                                  h_input, params['classes'], errors)

        # Make sure the user is allowed to access this form.
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            # FIXME: Raise HTTPError instead?
            self.send_error(401, "You're not authorized to view this form")
            return

        html_errors = u''
        if errors:
            html_errors = u'<ul>'
            for error in errors:
                html_errors += u'<li class="error">{0}</li>'.format(error)
            html_errors += u'</ul>'

        output = html_form.format(
            header=html_header.format(title=form_config.title,
                                      custom_css=form_config.custom_css),
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
        if not self.auth():
            return

        form_config = self.scriptform.get_form_config()
        form_name = form_values.getfirst('form_name', None)
        form_def = form_config.get_form_def(form_name)
        if form_def.allowed_users is not None and \
           self.username not in form_def.allowed_users:
            # FIXME: Raise HTTPError instead?
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
            if field.filename is not None:
                # Field is an uploaded file. Stream it to a temp file if
                # something was actually uploaded
                if field.filename == '':
                    continue
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

            # Log the callback and its parameters for auditing purposes.
            log = logging.getLogger('CALLBACK_AUDIT')
            log.info("Calling script {0}".format(form_def.script))
            log.info("User: {0}".format(getattr(self.request, 'username', 'None')))
            log.info("Variables: {0}".format(dict(form_values.items())))

            result = form_config.callback(form_name, form_values, self.wfile, self.wfile)
            if form_def.output != 'raw':
                # Ignore everything if we're doing raw output, since it's the
                # scripts responsibility.
                if result['exitcode'] != 0:
                    msg = u'<span class="error">{0}</span>'.format(cgi.escape(result['stderr'].decode('utf8')))
                else:
                    if form_def.output == 'escaped':
                        msg = u'<pre>{0}</pre>'.format(cgi.escape(result['stdout'].decode('utf8')))
                    else:
                        # Non-escaped output (html, usually)
                        msg = result['stdout'].decode('utf8')

                output = html_submit_response.format(
                    header=html_header.format(title=form_config.title,
                                              custom_css=form_config.custom_css),
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
            form_values.pop('form_name')
            self.h_form(form_name, form_errors, **form_values)

        # Clean up uploaded files
        for file_name in tmp_files:
            if os.path.exists(file_name):
                os.unlink(file_name)

    def h_static(self, fname):
        """Serve static files"""
        if not self.auth():
            return

        form_config = self.scriptform.get_form_config()

        if not form_config.static_dir:
            # FIXME: Raise Error
            self.send_error(501, "Static file serving not enabled")
            return

        if '..' in fname:
            # FIXME: Raise Error
            self.send_error(403, "Invalid file name")
            return

        path = os.path.join(form_config.static_dir, fname)
        if not os.path.exists(path):
            # FIXME: Raise Error
            self.send_error(404, "Not found")
            return

        f = file(path, 'r')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f.read())
