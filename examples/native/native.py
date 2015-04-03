#!/usr/bin/python

import scriptform
import sys

def job_import(values, request):
    return "Importing into database '{}'".format(values['target_db'])

def job_export(values, request):
    size = 4096 * 10000
    request.wfile.write('HTTP/1.0 200 Ok\n')
    request.wfile.write('Content-Type: application/octet-stream\n')
    request.wfile.write('Content-Disposition: attachment; filename="large_file.dat"\n')
    request.wfile.write('Content-Length: {0}\n\n'.format(size))

    f = file('/dev/urandom', 'r')
    sent_size = 0
    while True:
        buf = f.read(4096)
        if sent_size >= size:
            break
        request.wfile.write(buf)
        sent_size += 4096

def job_add_user(values, request):
    username = values['username']
    password1 = values['password1']
    password2 = values['password2']

    if not password1:
        raise Exception("Empty password specified")

    if password1 != password2:
        raise Exception("Passwords do not match.")

    # We do some stuff here.

    return "User created"

if __name__ == "__main__":
    callbacks = {
        'import': job_import,
        'export': job_export,
        'add_user': job_add_user
    }
    sf = scriptform.ScriptForm('native.json', callbacks)
    sf.run(listen_port=8000)
