import logging
import sys
import unittest
from StringIO import StringIO
import json
import os
import copy
import thread
import time
import requests
import StringIO
import re


class FormConfigTestCase(unittest.TestCase):
    """
    Test the proper low-level handling of form configurations such as loading,
    callbacks, etc.
    """
    @classmethod
    def tearDownClass(cls):
        if os.path.exists('tmp_stdout'):
            os.unlink('tmp_stdout')
        if os.path.exists('tmp_stderr'):
            os.unlink('tmp_stderr')

    def testNoSuchForm(self):
        """Getting non-existing form should raise ValueError"""
        sf = scriptform.ScriptForm('test_formconfig_hidden.json')
        fc = sf.get_form_config()
        self.assertRaises(ValueError, fc.get_form_def, 'nonexisting')

    def testMissingScript(self):
        """Missing script callbacks should raise an OSError"""
        self.assertRaises(OSError, scriptform.ScriptForm, 'test_formconfig_missingscript.json')

    def testNoExec(self):
        """Non-executable script callbacks should raise an FormConfigError"""
        from formconfig import FormConfigError
        self.assertRaises(FormConfigError, scriptform.ScriptForm, 'test_formconfig_noexec.json')

    def testHidden(self):
        """Hidden forms should not show up in the list of forms"""
        sf = scriptform.ScriptForm('test_formconfig_hidden.json')
        fc = sf.get_form_config()
        self.assertTrue(fc.get_visible_forms() == [])

    def testCallbackStore(self):
        """Test a callback that returns output in strings"""
        sf = scriptform.ScriptForm('test_formconfig_callback.json')
        fc = sf.get_form_config()
        fd = fc.get_form_def('test_store')
        res = runscript.run_script(fd, {})
        self.assertEquals(res['exitcode'], 33)
        self.assertTrue('stdout' in res['stdout'])
        self.assertTrue('stderr' in res['stderr'])

    def testCallbackRaw(self):
        """Test a callback that returns raw output"""
        sf = scriptform.ScriptForm('test_formconfig_callback.json')
        fc = sf.get_form_config()
        fd = fc.get_form_def('test_raw')
        stdout = file('tmp_stdout', 'w+') # can't use StringIO
        stderr = file('tmp_stderr', 'w+')
        exitcode = runscript.run_script(fd, {}, stdout, stderr)
        stdout.seek(0)
        stderr.seek(0)
        self.assertTrue(exitcode == 33)
        self.assertTrue('stdout' in stdout.read())

    def testCallbackMissingParams(self):
        """
        """
        sf = scriptform.ScriptForm('test_formconfig_callback.json')
        fc = sf.get_form_config()
        fd = fc.get_form_def('test_raw')
        self.assertRaises(ValueError, runscript.run_script, fd, {})


class FormDefinitionTest(unittest.TestCase):
    """
    Form Definition tests. Mostly directly testing if validations work.
    """
    def setUp(self):
        self.sf = scriptform.ScriptForm('test_formdefinition_validate.json')
        self.fc = self.sf.get_form_config()

    def testUnknownFieldError(self):
        fd = self.fc.get_form_def('test_required')
        self.assertRaises(KeyError, fd.get_field_def, 'nosuchfield')

    def testRequired(self):
        fd = self.fc.get_form_def('test_required')
        form_values = {}
        errors, values = fd.validate(form_values)
        self.assertIn('string', errors)
        self.assertIn('required', errors['string'][0])

    def testValidateStringMin(self):
        fd = self.fc.get_form_def('test_val_string')
        form_values = {"val_string": "123"}
        errors, values = fd.validate(form_values)
        self.assertIn('val_string', errors)
        self.assertIn('Minimum', errors['val_string'][0])

    def testValidateStringMax(self):
        fd = self.fc.get_form_def('test_val_string')
        form_values = {"val_string": "1234567"}
        errors, values = fd.validate(form_values)
        self.assertIn('val_string', errors)
        self.assertIn('Maximum', errors['val_string'][0])

    def testValidateStringValue(self):
        fd = self.fc.get_form_def('test_val_string')
        form_values = {"val_string": "1234"}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_string', errors)
        self.assertEquals(values['val_string'], "1234")

    def testValidateIntegerInvalid(self):
        fd = self.fc.get_form_def('test_val_integer')
        form_values = {"val_integer": 'three'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_integer', errors)
        self.assertIn('Must be a', errors['val_integer'][0])

    def testValidateIntegerMin(self):
        fd = self.fc.get_form_def('test_val_integer')
        form_values = {"val_integer": 3}
        errors, values = fd.validate(form_values)
        self.assertIn('val_integer', errors)
        self.assertIn('Minimum', errors['val_integer'][0])

    def testValidateIntegerMax(self):
        fd = self.fc.get_form_def('test_val_integer')
        form_values = {"val_integer": 7}
        errors, values = fd.validate(form_values)
        self.assertIn('val_integer', errors)
        self.assertIn('Maximum', errors['val_integer'][0])

    def testValidateIntegerValue(self):
        fd = self.fc.get_form_def('test_val_integer')
        form_values = {"val_integer": 6}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_integer', errors)
        self.assertEquals(values['val_integer'], 6)

    def testValidateFloatInvalid(self):
        fd = self.fc.get_form_def('test_val_float')
        form_values = {"val_float": 'four'}
        errors, values = fd.validate(form_values)
        self.assertTrue('val_float' in errors)
        self.assertTrue('Must be a' in errors['val_float'][0])

    def testValidateFloatMin(self):
        fd = self.fc.get_form_def('test_val_float')
        form_values = {"val_float": 2.05}
        errors, values = fd.validate(form_values)
        self.assertTrue('val_float' in errors)
        self.assertTrue('Minimum' in errors['val_float'][0])

    def testValidateFloatMax(self):
        fd = self.fc.get_form_def('test_val_float')
        form_values = {"val_float": 2.31}
        errors, values = fd.validate(form_values)
        self.assertIn('val_float', errors)
        self.assertIn('Maximum', errors['val_float'][0])

    def testValidateFloatValue(self):
        fd = self.fc.get_form_def('test_val_float')
        form_values = {"val_float": 2.29}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_float', errors)
        self.assertEquals(values['val_float'], 2.29)

    def testValidateDateInvalid(self):
        fd = self.fc.get_form_def('test_val_date')
        form_values = {"val_date": '2015-001'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_date', errors)
        self.assertIn('Invalid date', errors['val_date'][0])

    def testValidateDateMin(self):
        fd = self.fc.get_form_def('test_val_date')
        form_values = {"val_date": '2015-03-01'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_date', errors)
        self.assertIn('Minimum', errors['val_date'][0])

    def testValidateDateMax(self):
        fd = self.fc.get_form_def('test_val_date')
        form_values = {"val_date": '2015-03-06'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_date', errors)
        self.assertIn('Maximum', errors['val_date'][0])

    def testValidateDateValue(self):
        import datetime
        fd = self.fc.get_form_def('test_val_date')
        form_values = {"val_date": '2015-03-03'}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_date', errors)
        self.assertEquals(values['val_date'], datetime.date(2015, 3, 3))

    def testValidateSelectValue(self):
        fd = self.fc.get_form_def('test_val_select')
        form_values = {"val_select": 'option_a'}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_select', errors)
        self.assertEquals(values['val_select'], 'option_a')

    def testValidateSelectInvalid(self):
        fd = self.fc.get_form_def('test_val_select')
        form_values = {"val_select": 'option_c'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_select', errors)
        self.assertIn('Invalid value', errors['val_select'][0])

    def testValidateCheckbox(self):
        fd = self.fc.get_form_def('test_val_checkbox')
        form_values = {"val_checkbox": 'on'}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_checkbox', errors)
        self.assertEquals(values['val_checkbox'], 'on')

    def testValidateCheckboxDefaultOn(self):
        fd = self.fc.get_form_def('test_val_checkbox_on')
        form_values = {"val_checkbox_on": 'off'}
        errors, values = fd.validate(form_values)
        self.assertNotIn('val_checkbox_on', errors)
        self.assertEquals(values['val_checkbox_on'], 'off')

    def testValidateCheckboxInvalid(self):
        fd = self.fc.get_form_def('test_val_checkbox')
        form_values = {"val_checkbox": 'true'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_checkbox', errors)
        self.assertIn('Invalid value', errors['val_checkbox'][0])

    def testValidateTextMin(self):
        fd = self.fc.get_form_def('test_val_text')
        form_values = {"val_text": '1234'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_text', errors)
        self.assertIn('Minimum', errors['val_text'][0])

    def testValidateTextMax(self):
        fd = self.fc.get_form_def('test_val_text')
        form_values = {"val_text": '12345678901'}
        errors, values = fd.validate(form_values)
        self.assertIn('val_text', errors)
        self.assertIn('Maximum', errors['val_text'][0])

    def testValidateFileMissingFile(self):
        fd = self.fc.get_form_def('test_val_file')
        form_values = {}
        errors, values = fd.validate(form_values)
        self.assertIn('val_file', errors)
        self.assertIn('required', errors['val_file'][0])

    def testValidateFileMissingFileName(self):
        fd = self.fc.get_form_def('test_val_file')
        form_values = {'val_file': 'foo'}
        self.assertRaises(KeyError, fd.validate, form_values)


class FormDefinitionFieldMissingProperty(unittest.TestCase):
    """
    """
    def testMissing(self):
        self.assertRaises(KeyError, scriptform.ScriptForm, 'test_formdefinition_missing_title.json')


class WebAppTest(unittest.TestCase):
    """
    Test the web app by actually running the server and making web calls to it.
    """
    @classmethod
    def setUpClass(cls):
        cls.auth_admin = requests.auth.HTTPBasicAuth('admin', 'admin')
        cls.auth_user = requests.auth.HTTPBasicAuth('user', 'user')

        def server_thread(sf):
            sf.run(listen_port=8002)
        cls.sf = scriptform.ScriptForm('test_webapp.json')
        thread.start_new_thread(server_thread, (cls.sf, ))
        # Wait until the webserver is ready
        while True:
            time.sleep(0.1)
            if cls.sf.running:
                break

    @classmethod
    def tearDownClass(cls):
        cls.sf.shutdown()
        while True:
            time.sleep(0.1)
            if not cls.sf.running:
                break

    def testError404(self):
        r = requests.get('http://localhost:8002/nosuchurl')
        self.assertEqual(r.status_code, 404)
        self.assertIn('Not found', r.text)

    def testError401(self):
        r = requests.get('http://localhost:8002/')
        self.assertEqual(r.status_code, 401)

    def testAuthFormNoAuthGet(self):
        r = requests.get('http://localhost:8002/form?form_name=admin_only')
        self.assertEqual(r.status_code, 401)

    def testAuthFormNoAuthPost(self):
        data = {"form_name": 'admin_only'}
        r = requests.post('http://localhost:8002/submit', data)
        self.assertEqual(r.status_code, 401)

    def testAuthFormUnauthorizedGet(self):
        r = requests.get('http://localhost:8002/form?form_name=admin_only', auth=self.auth_user)
        self.assertEqual(r.status_code, 403)

    def testAuthFormUnauthorizedPost(self):
        data = {"form_name": 'admin_only'}
        r = requests.post('http://localhost:8002/submit', data, auth=self.auth_user)
        self.assertEqual(r.status_code, 403)

    def testHidden(self):
        """Hidden forms shouldn't appear in the output"""
        r = requests.get('http://localhost:8002/', auth=self.auth_user)
        self.assertNotIn('Hidden form', r.text)

    def testShown(self):
        """Non-hidden forms should appear in the output"""
        r = requests.get('http://localhost:8002/', auth=self.auth_user)
        self.assertIn('Output escaped', r.text)

    def testRender(self):
        r = requests.get('http://localhost:8002/form?form_name=validate', auth=self.auth_user)
        self.assertIn('Validated form', r.text)
        self.assertIn('This form is heavily validated', r.text)
        self.assertIn('name="string"', r.text)

    def testValidateCorrectData(self):
        data = {
            "form_name": 'validate',
            "string": "12345",
            "integer": "12",
            "float": "0.6",
            "date": "2015-01-02",
            "text": "1234567890",
            "password": "12345",
            "radio": "One",
            "checkbox": "on",
            "select": "option_a",
        }

        import random
        f = file('data.csv', 'w')
        for i in range(1024):
            f.write(chr(random.randint(0, 255)))
        f.close()

        files = {'file': open('data.csv', 'rb')}
        r = requests.post("http://localhost:8002/submit", data=data, files=files, auth=self.auth_user)

        self.assertIn('string=12345', r.text)
        self.assertIn('integer=12', r.text)
        self.assertIn('float=0.6', r.text)
        self.assertIn('date=2015-01-02', r.text)
        self.assertIn('text=1234567890', r.text)
        self.assertIn('password=12345', r.text)
        self.assertIn('radio=One', r.text)
        self.assertIn('checkbox=on', r.text)
        self.assertIn('select=option_a', r.text)

        os.unlink('data.csv')

    def testValidateIncorrectData(self):
        data = {
            "form_name": 'validate',
            "string": "12345678",
            "integer": "9",
            "float": "1.1",
            "date": "2015-02-02",
            "radio": "Ten",
            "text": "123456789",
            "password": "1234",
            "checkbox": "invalidvalue",
            "select": "invalidvalue",
        }

        import random
        f = file('data.txt', 'w')
        for i in range(1024):
            f.write(chr(random.randint(0, 255)))
        f.close()

        files = {'file': open('data.txt', 'rb')}
        r = requests.post("http://localhost:8002/submit", data=data, files=files, auth=self.auth_user)

        self.assertIn('Maximum length is 7', r.text)
        self.assertIn('Minimum value is 10', r.text)
        self.assertIn('Maximum value is 1.0', r.text)
        self.assertIn('Maximum value is 2015-02-01', r.text)
        self.assertIn('Invalid value for radio button: Ten', r.text)
        self.assertIn('Minimum length is 10', r.text)
        self.assertIn('Minimum length is 5', r.text)
        self.assertIn('Only file types allowed: csv', r.text)
        self.assertIn('Invalid value for radio button', r.text)
        self.assertIn('Invalid value for dropdown', r.text)

        os.unlink('data.txt')

    def testValidateRefill(self):
        """
        Ensure that field values are properly repopulated if there were any
        errors in validation.
        """
        data = {
            "form_name": 'validate',
            "string": "123",
            "integer": "12",
            "float": "0.6",
            "date": "2015-01-02",
            "text": "1234567890",
            "password": "12345",
            "radio": "One",
            "checkbox": "on",
            "select": "option_b",
        }

        import random
        f = file('data.txt', 'w')
        for i in range(1024):
            f.write(chr(random.randint(0, 255)))
        f.close()

        files = {'file': open('data.txt', 'rb')}
        r = requests.post("http://localhost:8002/submit", data=data, files=files, auth=self.auth_user)
        self.assertIn('value="123"', r.text)
        self.assertIn('value="12"', r.text)
        self.assertIn('value="0.6"', r.text)
        self.assertIn('value="2015-01-02"', r.text)
        self.assertIn('>1234567890<', r.text)
        self.assertIn('value="12345"', r.text)
        self.assertIn('value="on"', r.text)
        self.assertIn('selected>Option B', r.text)

        os.unlink('data.txt')

    def testOutputEscaped(self):
        """Form with 'escaped' output should have HTML entities escaped"""
        data = {
            "form_name": 'output_escaped',
            "string": '<foo>'
        }
        r = requests.post('http://localhost:8002/submit', data, auth=self.auth_user)
        self.assertIn('string=&lt;foo&gt;', r.text)

    def testOutputRaw(self):
        data = {
            "form_name": 'output_raw',
            "string": '<foo>'
        }
        r = requests.post('http://localhost:8002/submit', data, auth=self.auth_user)
        self.assertIn('string=<foo>', r.text)

    def testOutputHTML(self):
        data = {
            "form_name": 'output_html',
            "string": '<foo>'
        }
        r = requests.post('http://localhost:8002/submit', data, auth=self.auth_user)
        self.assertIn('string=<foo>', r.text)

    def testUpload(self):
        import random
        f = file('data.raw', 'w')
        for i in range(1024):
            f.write(chr(random.randint(0, 255)))
        f.close()

        data = {
            "form_name": "upload"
        }
        files = {'file': open('data.raw', 'rb')}
        r = requests.post("http://localhost:8002/submit", files=files, data=data, auth=self.auth_user)
        self.assertIn('SAME', r.text)
        os.unlink('data.raw')

    def testStaticValid(self):
        r = requests.get("http://localhost:8002/static?fname=ssh_server.png", auth=self.auth_user)
        self.assertEquals(r.status_code, 200)
        f_served = b''
        for c in r.iter_content():
            f_served += c

        f_orig = file('static/ssh_server.png', 'rb').read()
        self.assertEquals(f_orig, f_served)

    def testStaticInvalidFilename(self):
        r = requests.get("http://localhost:8002/static?fname=../../ssh_server.png", auth=self.auth_user)
        self.assertEquals(r.status_code, 403)

    def testStaticInvalidNotFound(self):
        r = requests.get("http://localhost:8002/static?fname=nosuchfile.png", auth=self.auth_user)
        self.assertEquals(r.status_code, 404)

    def testHiddenField(self):
        r = requests.get('http://localhost:8002/form?form_name=hidden_field', auth=self.auth_user)
        self.assertIn('class="hidden"', r.text)

    def testCallbackFail(self):
        data = {
            "form_name": "callback_fail"
        }
        r = requests.post("http://localhost:8002/submit", data=data, auth=self.auth_user)
        self.assertIn('<span class="error">stderr output\n</span>', r.text)


class WebAppSingleTest(unittest.TestCase):
    """
    Test that Scriptform doesn't show us a list of forms, but directly shows us
    the form is there's only one.
    """
    @classmethod
    def setUpClass(cls):
        def server_thread(sf):
            sf.run(listen_port=8002)
        cls.sf = scriptform.ScriptForm('test_webapp_singleform.json')
        thread.start_new_thread(server_thread, (cls.sf, ))
        # Wait until the webserver is ready
        while True:
            time.sleep(0.1)
            if cls.sf.running:
                break

    @classmethod
    def tearDownClass(cls):
        cls.sf.shutdown()
        while True:
            time.sleep(0.1)
            if not cls.sf.running:
                break

    def testSingleForm(self):
        """
        Ensure that Scriptform directly shows the form if there is only one.
        """
        r = requests.get("http://localhost:8002/")
        self.assertIn('only_form', r.text)

    def testStaticDisabled(self):
        """
        """
        r = requests.get("http://localhost:8002/static?fname=nosuchfile.png")
        self.assertEquals(r.status_code, 501)


if __name__ == '__main__':
    logging.basicConfig(level=logging.FATAL,
                        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                        filename='test.log',
                        filemode='a')
    import coverage
    cov = coverage.coverage(omit=['*test*', 'main', '*/lib/python*'])
    cov.start()

    sys.path.insert(0, '../src')
    import scriptform
    import runscript
    unittest.main(exit=True)

    cov.stop()
    cov.save()

    print cov.report()
    try:
        print cov.html_report()
    except coverage.misc.CoverageException, e:
        if "Couldn't find static file 'jquery.hotkeys.js'" in e.message:
            pass
        else:
            raise
