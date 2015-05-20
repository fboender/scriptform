import sys
import unittest
sys.path.insert(0, '../src')
import scriptform
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

def run_server(sf):
    def server_thread(sf):
        sf.run(listen_port=8002)
    thread.start_new_thread(server_thread, (sf, ))
    # Wait until the webserver is ready
    while True:
        time.sleep(0.1)
        if sf.running:
            break


class FormConfigTestCase(unittest.TestCase):
    def testMissing(self):
        """Missing script callbacks should raise an OSError"""
        self.assertRaises(OSError, scriptform.ScriptForm, 'test_formconfig_missingscript.json')

    def testNoExec(self):
        """Non-executable script callbacks should raise an ScriptFormError"""
        self.assertRaises(scriptform.ScriptFormError, scriptform.ScriptForm, 'test_formconfig_noexec.json')

    def testHidden(self):
        """Hidden forms should not show up in the list of forms"""
        sf = scriptform.ScriptForm('test_formconfig_hidden.json')
        fc = sf.get_form_config()
        self.assertTrue(fc.get_visible_forms() == [])

    def testCallbackStore(self):
        sf = scriptform.ScriptForm('test_formconfig_callback.json')
        fc = sf.get_form_config()
        res = fc.callback('test_store', {})
        self.assertEquals(res['exitcode'], 33)
        self.assertTrue('stdout' in res['stdout'])
        self.assertTrue('stderr' in res['stderr'])

    #def testCallbackRaw(self):
    #    sf = scriptform.ScriptForm('test_formconfig_callback.json')
    #    fc = sf.get_form_config()
    #    stdout = StringIO.StringIO()
    #    stderr = StringIO.StringIO()
    #    res = fc.callback('test_raw', {}, stdout, stderr)
    #    stdout.seek(0)
    #    stderr.seek(0)
    #    self.assertTrue(res['exitcode'] == 33)
    #    print stdout.read()
    #    self.assertTrue('stdout' in stdout.read())


if __name__ == '__main__':
    unittest.main()
