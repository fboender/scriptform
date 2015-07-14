"""
Basic web server / framework.
"""

from SocketServer import ThreadingMixIn
import BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse
import cgi


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


class RequestHandler(BaseHTTPRequestHandler):
    """
    Basic web server request handler. Handles GET and POST requests. You should
    inherit from this class and implement h_ methods for handling requests.
    If no path is set, it dispatches to the 'index' or 'default' method.
    """
    def log_message(self, fmt, *args):
        """Overrides BaseHTTPRequestHandler which logs to the console. We log
        to our log file instead"""
        fmt = "{0} {1}"
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
