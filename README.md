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
- Completely standalone HTTP server; only required Python.
- Callbacks to any kind of script / program or to Python functions.
- User authentication support through Basic HTAuth.
- Validates form values before calling scripts.
- Uploaded files are automatically saved to temporary files, which are passed
  on to the callback.
- Multiple forms in a single JSON definition file.

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


Form definition file: `test_server.json`

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

We can now start ScriptForm to start serving the form over HTTP:

    $ scriptform -p8080 ./test_server.json

The user is presented with the following form:

![](https://raw.githubusercontent.com/fboender/scriptform/master/doc/screenshots/list.png)

When submitting the form, the results are displayed.

![](https://raw.githubusercontent.com/fboender/scriptform/master/doc/screenshots/form.png)

## Installation

### Requirements

ScriptForm requires:

* Python 2.6+ # FIXME

## Usage

### Authentication

Passwords are stored in plain text.

## License

ScriptForm is released under the MIT license.

Copyright (c) 20152 Ferry Boneder (ferry.boender@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

