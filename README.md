# ScriptForm


## About

A stand-alone webserver that automatically generates forms from JSON to serve
as frontends to scripts.

ScriptForm takes a JSON file which contains form definitions. It then
constructs web forms from this JSON and serves these to users. The user can
select a form and fill it out. When the user submits the form, it is validated
and the associated script is called. Data entered in the form is passed to the
script through the environment.

### Features

- Very rapidly construct forms with backends.
- Completely standalone HTTP server; only requires Python.
- Callbacks to any kind of script / program that supports environment
  variables.
- User authentication support through Basic HTAuth.
- Validates form values before calling scripts.
- Uploaded files are automatically saved to temporary files, which are passed
  on to the callback.
- Multiple forms in a single JSON definition file.
- Scripts can produce normal output, HTML output or stream their own HTTP
  response to the client. The last one lets you stream images or binaries to
  the browser.

### Use-cases

Scriptform is very flexible and as such serves many use-cases. Most of these
revolve around giving non-technical users a user friendly way to safely run
scripts on a server.

Here are some of the potential uses of Scriptform:

- Add / remove users from htpasswd files.
- Execute SQL snippets.
- View service status
- Upload data to be processed.
- Restart, enable and disable services.
- Trigger for batch processing.

## Example

The following example lets you add new users to a htpasswd file via ScriptForm.
It presents the user with a form to enter the user's details. When the form is
submitted, the `job_add_user.sh` script is called which adds the user to the
htpasswd file.


Form configuration file: `test_server.json`

    {
      "title": "Test server",
      "forms": {
        "add_user": {
          "title": "Add user",
          "description": "Add a user to the htpasswd file",
          "submit_title": "Add user",
          "script": "job_add_user.sh",
          "fields": [
            {"name": "username", "title": "Username", "type": "string"},
            {"name": "password1", "title": "Password", "type": "password"},
            {"name": "password2", "title": "Repeat password", "type": "password"}
          ]
        }
      }
    }

The script `job_add_user.sh`:

    #!/bin/sh

    if [ -z "$password1" ]; then
        echo "Empty password specified" >&2; exit 1
    fi
    if [ "$password1" != "$password2" ]; then
        echo "Passwords do not match" >&2; exit 1
    fi

    htpasswd -s -b .htpasswd $username $password1 || exit $?

    echo "User created or password updated"

Set some rights and create the initial `htpasswd` file:

    $ chmod 755 job_add_user.sh
    $ touch .htpasswd

We can now start ScriptForm to start serving the form over HTTP. By default it
starts as a daemon, so we specify the `-f` option to start it in the foreground
instead.

    $ scriptform -f -p8080 ./test_server.json

The user is presented with the following form:

![](https://raw.githubusercontent.com/fboender/scriptform/master/doc/screenshots/form.png)

When submitting the form, the results are displayed.

![](https://raw.githubusercontent.com/fboender/scriptform/master/doc/screenshots/result.png)

For more examples, see the [examples directory](https://github.com/fboender/scriptform/tree/master/examples)

For more screenshots, see the [screenshots Wiki page](https://github.com/fboender/scriptform/wiki/Screenshots)

## Installation

### Requirements

ScriptForm requires:

* Python 2.6+

No other libraries are required. Python v2.6+ is generally available by default
on almost every major linux distribution. For other platforms Python is almost
certainly available.

## Usage

Usage:

    Usage: ./scriptform.py [option] (--start|--stop) <form_definition.json>
           ./scriptform.py --generate-pw

    Options:
      -h, --help            show this help message and exit
      -g, --generate-pw     Generate password
      -p PORT, --port=PORT  Port to listen on
      -f, --foreground      Run in foreground (debugging)
      --pid-file=PID_FILE   Pid file
      --log-file=LOG_FILE   Log file
      --start               Start daemon
      --stop                Stop daemon


ScriptForm can run both in daemon mode or in the foreground. In daemon mode, we
can control ScriptForm with the `--start` and `--stop` options. By default it
runs on port 80, which we can change with the `-p` option.

    $ ./scriptform -p8000 ./test_server.json

This puts ScriptForm in the background as a daemon. It creates a PID file and a
log file.

    $ tail scriptform.py.log
    2015-04-08 07:57:27,160:DAEMON:INFO:Starting
    2015-04-08 07:57:27,161:DAEMON:INFO:PID = 5614
    2015-04-08 07:57:27,162:SCRIPTFORM:INFO:Listening on 0.0.0.0:8000

In order to stop the daemon:

    $ ./scriptform --stop

We can control the location of the PID file and log file with the `--pid-file`
and `--log-file` options. If we don't specify these, ScriptForm will create
them in the local directory.

To run ScriptForm in the foreground, specify the `-f` option. 

If you're going to use basic authentication, you can generate a password for
your user with the `--generate-pw` option:

    $ ./scriptform.py --generate-pw
    Password: 
    Repeat password: 
    2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae

You can paste the generated password into the password field. For more
information, see the User Manual.

## Security

ScriptForm is only as secure as you write your scripts. Although form values
are validated before calling scripts, many possible security problems should be
taken into consideration. As such, you should *never* expose ScriptForm to the
public internet. Its intended end users should be people you trust at least to
a certain degree.

## License

ScriptForm is released under the MIT license.

Copyright (c) 20152 Ferry Boneder (ferry.boender@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

