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
        config = copy.deepcopy(base_config)
        config["forms"][0]["script"] = "nonexisting.sh"
        file('test.json', 'w').write(json.dumps(config))
        self.assertRaises(OSError, scriptform.ScriptForm, 'test.json')

    def testNoExec(self):
        """Nonn-executable script callbacks should raise an ScriptFormError"""
        config = copy.deepcopy(base_config)
        config["forms"][0]["script"] = "test_noexec.sh"
        file('test.json', 'w').write(json.dumps(config))
        self.assertRaises(scriptform.ScriptFormError, scriptform.ScriptForm, 'test.json')

    def testHidden(self):
        """Hidden forms should not show up in the list of forms"""
        config = copy.deepcopy(base_config)
        config["forms"][0]["hidden"] = True
        file('test.json', 'w').write(json.dumps(config))
        sf = scriptform.ScriptForm('test.json')
        fc = sf.get_form_config()
        self.assertTrue(fc.get_visible_forms() == [])

class ScriptFormTestCase(unittest.TestCase):
    def testShutdown(self):
        config = copy.deepcopy(base_config)
        file('test.json', 'w').write(json.dumps(config))
        sf = scriptform.ScriptForm('test.json')
        run_server(sf)
        sf.shutdown()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
