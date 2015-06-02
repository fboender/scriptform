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

base_config = {
    "title": "test",
    "forms": [
        {
            "name": "test",
            "title": "title",
            "description": "description",
            "script": "test.sh",
            "fields": [],
        }
    ]
}


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

    def testMissing(self):
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
        res = fc.callback('test_store', {})
        self.assertEquals(res['exitcode'], 33)
        self.assertTrue('stdout' in res['stdout'])
        self.assertTrue('stderr' in res['stderr'])

    def testCallbackRaw(self):
        """Test a callback that returns raw output"""
        sf = scriptform.ScriptForm('test_formconfig_callback.json')
        fc = sf.get_form_config()
        stdout = file('tmp_stdout', 'w+') # can't use StringIO
        stderr = file('tmp_stderr', 'w+')
        exitcode = fc.callback('test_raw', {}, stdout, stderr)
        stdout.seek(0)
        stderr.seek(0)
        self.assertTrue(exitcode == 33)
        self.assertTrue('stdout' in stdout.read())

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

    def testAuthFormWrongAuthGet(self):
        r = requests.get('http://localhost:8002/form?form_name=admin_only', auth=self.auth_user)
        self.assertEqual(r.status_code, 401)

    def testAuthFormWrongAuthPost(self):
        data = {"form_name": 'admin_only'}
        r = requests.post('http://localhost:8002/submit', data, auth=self.auth_user)
        self.assertEqual(r.status_code, 401)

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

    def testStatic(self):
        r = requests.get("http://localhost:8002/static?fname=ssh_server.png", auth=self.auth_user)
        self.assertEquals(r.status_code, 200)
        f_served = b''
        for c in r.iter_content():
            f_served += c

        f_orig = file('static/ssh_server.png', 'rb').read()
        self.assertEquals(f_orig, f_served)


if __name__ == '__main__':
    import coverage
    cov = coverage.coverage(omit=['*test*', 'main'])
    cov.start()

    sys.path.insert(0, '../src')
    import scriptform
    unittest.main(exit=False)

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
