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
- Fix error (megacorp load employees no file specified)
  ----------------------------------------
  Exception happened during processing of request from ('127.0.0.1', 57639)
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
    File "/home/fboender/Temp/scriptform-0.3/webapp.py", line 162, in do_POST
      self._call(self.path.strip('/'), params={'form_values': form_values})
    File "/home/fboender/Temp/scriptform-0.3/webapp.py", line 198, in _call
      method_cb(**params)
    File "/home/fboender/Temp/scriptform-0.3/webapp.py", line 428, in h_submit
      form_errors, form_values = form_def.validate(values)
    File "/home/fboender/Temp/scriptform-0.3/formdefinition.py", line 57, in validate
      v = self._field_validate(field_name, form_values)
    File "/home/fboender/Temp/scriptform-0.3/formdefinition.py", line 75, in _field_validate
      return validate_cb(field_def, form_values)
    File "/home/fboender/Temp/scriptform-0.3/formdefinition.py", line 186, in validate_file
      value = form_values[field_def['name']]
  KeyError: u'csv_file'
  ----------------------------------------
