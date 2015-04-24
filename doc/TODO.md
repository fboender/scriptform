- Fix the following error:
    Exception happened during processing of request from ('127.0.0.1', 43319)
    Traceback (most recent call last):
      File "/usr/lib/python2.7/SocketServer.py", line 593, in process_request_thread
        self.finish_request(request, client_address)
      File "/usr/lib/python2.7/SocketServer.py", line 334, in finish_request
        self.RequestHandlerClass(request, client_address, self)
      File "/usr/lib/python2.7/SocketServer.py", line 649, in __init__
        self.handle()
      File "/usr/lib/python2.7/BaseHTTPServer.py", line 340, in handle
        self.handle_one_request()
      File "/usr/lib/python2.7/BaseHTTPServer.py", line 328, in handle_one_request
        method()
      File "../../src/scriptform.py", line 505, in do_POST
        self._call(self.path.strip('/'), params={'form_values': form_values})
      File "../../src/scriptform.py", line 541, in _call
        method_cb(**params)
      File "../../src/scriptform.py", line 764, in h_submit
        if field.filename:
    AttributeError: 'list' object has no attribute 'filename'
- Don't run as root.
- Validate max min of date in browser?
- Repopulate form fields on error.
- Debugging mode: automatically reload the form definition each time.
- Checkbox form input type.
