ScriptForm test example
=========================

This test example shows the usage of the `run_as` functionality. If we specify a `run_as` field in a form like so:


    "forms": [
        {
            "name": "run_as",
            "title": "Run as...",
            "description": "",
            "submit_title": "Run",
            "run_as": "man",
            "script": "job_run_as.py",
            "fields": []
        }
    ]

Scriptform will try to run the script as that user (in this case: `man`). This
requires Scriptform to be running as root. 

If no `run_as` is given in a script, Scriptform will execute scripts as the
current user (the one running Scriptform). If, however, Scriptform is being run
as root and you don't specify a `run_as` user, the scripts will run as user
`nobody` for security considerations!
