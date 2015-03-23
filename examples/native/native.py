#!/usr/bin/python

import scriptform

def job_import(values):
    return "Importing into database '{}'".format(values['target_db'])

def job_add_user(values):
    username = values['username']
    password1 = values['password1']
    password2 = values['password2']

    if not password1:
        return "Empty password specified."

    if password1 != password2:
        return "Passwords do not match."

    # We do some stuff here.

    return "User created"

if __name__ == "__main__":
    callbacks = {
        'import': job_import,
        'add_user': job_add_user
    }
    sf = scriptform.ScriptForm('native.json', callbacks)
    sf.run(listen_port=8080)
