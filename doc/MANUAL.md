# <a name="manual">Scriptform Manual</a>

This is the manual for version %%VERSION%%.




## Table of Contents

1. [Introduction](#intro)
    - [Terminology](#intro_terminology)
1. [Installation](#inst)
    - [Debian / Ubuntu](#inst_debian)
    - [Redhat / Centos](#inst_redhat)
    - [Other](#inst_other)
1. [Invocations](#invocations)
    - [Shell foreground](#invocations_foreground)
    - [Daemon](#invocations_daemon)
    - [Init script](#invocations_init)
        * [Debian / Ubuntu](#invocations_init_debian)
        * [RedHat / Centos](#invocations_init_redhat)
    - [Behind Apache](#invocations_apache)
1. [Tutorial](#tutorial)
    - [Your first form](#tutorial_firstform)
    - [Output types](#tutorial_output)
    - [Fields](#tutorial_fields)
    - [Uploads](#tutorial_uploads)
    - [Validation](#tutorial_validation)
    - [Further reading](#tutorial_further)
1. [Form config (JSON) files](#form_config)
1. [Field types](#field_types)
    - [String](#field_types_string)
    - [Integer](#field_types_integer)
    - [Float](#field_types_float)
    - [Date](#field_types_date)
    - [Radio](#field_types_radio)
    - [Checkbox](#field_types_checkbox)
    - [Select](#field_types_select)
    - [Text](#field_types_text)
    - [Password](#field_types_password)
    - [File](#field_types_file)
1. [Output](#output)
    - [Output types](#output_types)
    - [Exit codes](#output_exitcodes)
    - [Serving static files](#output_static_files)
1. [Script execution](#script_execution)
    - [Validation](#script_validation)
    - [Field Values](#script_fieldvalues)
    - [Execution security policy](#script_runas)
1. [Users](#users)
    - [Passwords](#users_passwords)
    - [Form limiting](#users_formlimit)
    - [Security considerations](#users_security)
    - [Pre-authentication with Apache](#users_preauth)
1. [Form customization](#cust)
    - [Custom CSS](#cust_css)
1. [Security](#security)





## <a name="intro">Introduction</a>

Scriptform is a stand-alone webserver that automatically generates forms from
JSON to serve as frontends to scripts.

ScriptForm takes a JSON file which contains form definitions. It then
constructs web forms from this JSON and serves these to users over HTTP. The
user can select a form and fill it out. When the user submits the form, it is
validated and the associated script is called. Data entered in the form is
passed to the script through the environment.

### <a name="intro_terminology">Terminology</a>

Scriptform uses various terminology to distinguish between different components
of the application.

* **Form configuration**: The form configuration is the JSON file you write
  that describes your forms. A single JSON file contains some global
  properties (such as the title), the forms you want to define and their fields.
* **Form definition**: A form definition describes a single form. Multiple form
  definitions can be given in a single form configuration. They are defined in
  the "forms" property of the form configuration. This "forms" property is a
  list of dictionaries.
* **Form field**: Form definitions can contain one of more form fields. These
  are the fields in which users can enter information. Scriptform supports a
  variety of different field types, such as 'string', 'integer', 'date', etc.






## <a name="inst">Installation and configuration</a>

### <a name="inst_requirements">Requirements</a>

ScriptForm requires:

* Python 2.6+

No other libraries are required. Python v2.6+ is generally available by default
on almost every major linux distribution. For other platforms Python is almost
certainly available.

### <a name="inst_debian">Debian / Ubuntu</a>

Download the .deb package from:

https://github.com/fboender/scriptform/releases

Either double-click the package in a file browser or open up a terminal and type:

    $ cd Downloads/
    $ sudo dpkg -i scriptform-*.deb

Scriptform is now installed. For the next steps, see:

* The tutorial on how to write form configuration files.
* Invocations for how to run Scriptform and how to start it at boot time

### <a name="inst_redhat">RedHat / Centos</a>

Download the .rpm package from:

https://github.com/fboender/scriptform/releases

Open up a terminal and type:

    $ cd Downloads/
    $ sudo rpm -i scriptform-*.rpm

Scriptform is now installed. For the next steps, see:

* The tutorial on how to write form configuration files.
* Invocations for how to run Scriptform and how to start it at boot time

### <a name="inst_other">Other Unix-like Operating Systems</a>

Install Python v2.6+.

Download the .tar.gz package from:

https://github.com/fboender/scriptform/releases

Open up a terminal and type:

    $ cd Downloads/
    $ tar -vxzf scriptform-*.tar.gz
    $ cd scriptform-X.Y
    $ sudo make install

Scriptform is now installed. For the next steps, see:

* The tutorial on how to write form configuration files.
* Invocations for how to run Scriptform and how to start it at boot time






## <a name="invocations">Invocations</a>

Upon starting Scriptform, it will change the working directory to the path
containing the form definition you've specified. It will read the form
definition and perform some basic sanity checks to see if, for instance, the
scripts you specified exist and are executable.

There are multiple ways of running ScriptForm. This chapter outlines the
various methods. They are listed in the order of least to most
production ready.

### <a name="invocations_foreground">Shell foreground</a>

Sriptform can be run directly from the shell in the foreground with the `-f`
(`--foreground`) option. This is most useful for testing and development:

    $ /usr/bin/scriptform -p8081 -f ./formdef.json

You can specify the `-r` option to automatically reload the JSON file upon each
request:

    $ /usr/bin/scriptform -p8081 -r -f ./formdef.json

### <a name="invocations_daemon">Daemon</a>

If you do not specify the `-f` option, Scriptform will go into the background:

    $ /usr/bin/scriptform -p8081 ./formdef.json
    $

A pid file will be written in the current directory, or to the file specified
by `--pid-file`. A log file will be written a .log file in the current
directory, or to the file specified by the `--log-file` option.

To stop the daemon, invoke the command with the `--stop` option. You must
specify at least the `--pid-file` option, if the daemon was started with one.

    $ /usr/bin/scriptform --pid-file /var/run/scriptform.pid --stop

### <a name="invocations_init">Init script</a>

#### <a name="invocations_init_debian">Debian / Ubuntu</a>

An example init script is provided in the *contrib* directory. For the Debian
package, you can find it in `/usr/share/doc/scriptform/`. To install it on
Debian-derived systems:

    sudo cp /usr/share/doc/scriptform/scriptform.init.d_debian /etc/init.d/scriptform
    sudo chmod 755 /etc/init.d/scriptform
    sudo update-rc.d scriptform defaults

Then, edit the init script and set the FORM_CONFIG variable.

    sudo vi /etc/init.d/scriptform
    FORM_CONFIG="/usr/local/scriptform/myscript/myscript.json

Finally, start it:

    sudo /etc/init.d/scriptform start

#### <a name="invocations_init_redhat">RedHat / CentOs</a>

Install the init script:

    sudo cp /usr/share/doc/scriptform/scriptform.init.d_redhat /etc/init.d/scriptform
    sudo chmod 755 /etc/init.d/scriptform

Then, edit the init script so it points to your form configuration file:

    sudo vi /etc/init.d/scriptform
    FORM_CONFIG="/usr/local/scriptform/myscript/myscript.json

Finally, enable the init script to run at boot time:

    sudo chkconfig --add scriptform
    sudo chkconfig scriptform on

Now we can start it:

    sudo /etc/init.d/scriptform start
    Starting scriptform: 



### <a name="invocations_apache">Behind Apache</a>

Scriptform does not support HTTPS / SSL, so for production environments you
might want to run it behind an Apache server that has SSL enabled. To do so,
you start Scriptform as a daemon and then forward requests to it from Apache:

    $ sudo /etc/init.d/scriptform start

Enable Apache modules mod_proxy and mod_proxy_http:

    $ sudo a2enmod proxy
    $ sudo a2enmod proxy_http

Configure:

    Redirect permanent /scriptform /scriptform/
    ProxyPass /scriptform/ http://localhost:8081/
    ProxyPassReverse /scriptform/ http://localhost:8081/

Make sure the path ends in a slash! (That's what the redirect is for).
Otherwise, you may encounter the following error:

    +  TypeError: index() got an unexpected keyword argument 'form_name'




## <a name="tutorial">Tutorial</a>

### <a name="tutorial_firstform">Your first form</a>

This tutorial assumes you've already installed Scriptform on your system.

Let's start off by creating a new form configuration file. Create a directory:

    $ mkdir sf_tutorial
    $ cd sf_tutorial

Edit a new file called `sf_tutorial.json` in your favorite editor and put the
following in:


    {
      "title": "Tutorial",
      "forms": [
        {
          "name": "System information",
          "title": "System information",
          "description": "Show information about the operating system",
          "script": "job_sysinfo.sh",
          "fields": []
        }
      ]
    }

This is a form configuration with a single form definition "System
information". The form has no fields; we'll get to that later. First, let's
implement the `job_sysinfo.sh` script so we can perform a form callback.

Edit a new file in the same directory called `job_sysinfo.sh`:

    #!/bin/sh
    
    HOSTNAME=$(hostname -f)
    MEM=$(free -h)
    DISK=$(df -h)
    
    cat << END_OF_TEXT
    Hostname
    ========
    
    $HOSTNAME
    
    
    Memory
    ======
    
    $MEM
    
    
    Disk
    ====
    
    $DISK
    END_OF_TEXT

Fix the permisions so it is executable:

    $ chmod 755 ./job_sysinfo.sh

Now start Scriptform with our newly created form configuration file:

    $ scriptform -p8081 -f -r ./sf_tutorial.json

This starts the built-in webserver which will serve the form on port 8081. When
you open it in your browser (http://127.0.0.1:8081/) you will immediately see
the form. If we had multiple forms in this form configuration, you would first
see a list of all the forms.

The `-p` option controls the port on which Scriptform will listen. Normally,
Scriptform would go into the background and run as a daemon. We can surpress
this with the `-f` (foreground) switch, which makes it easier to stop
Scriptform by pressing Ctrl-c. The `-r` option tells Scriptform to reload the
form configuration file on each request. This makes development much easier,
since you won't have to stop and restart Scriptform whenever you make a change.


### <a name="tutorial_output">Output types</a>

The output of our first form isn't exactly good-looking. We can change that by
changing the output type of our form. There are three types: escaped, html and
raw. Let's change our output to HTML.

Open the `sf_tutorial.json` file and add an `output` property to the form:

    ...
    "script": "job_sysinfo.sh",
    "output": "html",
    "fields": []
    ...

Now modify the `job_sysinfo.sh` script to output HTML instead of plain text:

    cat << END_OF_TEXT
    <h3>Hostname</h3>
    <pre>$HOSTNAME</pre>
    
    <h3>Memory</h3>
    <pre>$MEM</pre>
    
    <h3>Disk</h3>
    <pre>$DISK</pre>
    END_OF_TEXT

Open http://127.0.0.1:8081 in your browser and submit the form. That looks a
little better, doesn't it? The `html` output type lets you embed HTML in the
output of the script. The default output type is `escaped`, which escaped any
HTML and just outputs plain text wrapped in a Scriptform response header and
footer. The last output type is `raw`, in which case Scriptform will send the
*exact* output of your script directly to the browser. This means your script
should not just output a result, but also the required HTTP headers to properly
display it. This lets your send binary files (images, downloads, etc) to the
browser.

Read more about output types in the '[Output types](#output_types)' section.

### <a name="tutorial_fields">Fields</a>

As you've seen, we've kept the `fields` option empty in the previous examples.
The `fields` option lets us specify input fields that will appear in the form.
Every field has at least a `name`, `title` and `type`. Many fields support
additional options for validation, etc.

There are fields available for many types: strings, numbers, dates, dropdown
boxes, file uploads, etc. For a full list see the [Field types](#field_types)
section of the user manual.

The simplest is the `string` field. This field type simply lets the user enter
a value. Put the following in the `sf_tutorial.json` file, replacing the
original content (or create a new json file):

    {
      "title": "Tutorial step 3",
      "forms": [
        {
          "name": "hello_world",
          "title": "Hello, world!",
          "description": "Greetings",
          "script": "job_helloworld.sh",
          "fields": [
            {
              "name": "name",
              "title": "Name",
              "type": "string"
            }
          ]
        }
      ]
    }

Create the `job_helloworld.sh` script:

    #!/bin/sh
    
    if [ -z "$name" ]; then
        name="world"
    fi
    
    echo "Hello, $name!"

Make it executable:

    $ chmod 755 job_helloworld.sh

And start Scriptform (not required if it's still running and you're using the
same .json file):

    $ scriptform -p8081 -f -r ./sf_tutorial.json

Point your browser to http://127.0.0.01:8081. Try submitting the form with and
without entering a name. 

As you can see, Scriptform makes form values available to scripts through the
environment. This makes it easy to implement scripts in any language you'd
like. For example, this is what a script implemented in Python would look like:

    #!/usr/bin/env python
    
    import os
    
    name = os.environ['name']
    if not name:
        name = "world"
    
    print "Hello, {0}!".format(name)

### <a name="tutorial_upload">Upload</a>

Let's extend our form with a file upload. Modify `sf_tutorial.json` and add an upload field:

    ...
    {
      "name": "upload",
      "title": "Upload a file",
      "type": "file"
    }
    ...

We'll also change it to run a different script:

    ...
    "script": "job_upload.py",
    ...

The entire file now looks like this:

    {
      "title": "Tutorial step 4: Uploads",
      "forms": [
        {
          "name": "hello_world",
          "title": "Hello, world!",
          "description": "Greetings",
          "script": "job_upload.sh",
          "fields": [
            {
              "name": "name",
              "title": "Name",
              "type": "string"
            },
            {
              "name": "upload",
              "title": "Upload a file",
              "type": "file"
            }
          ]
        }
      ]
    }

We'll make the script output the size of the file in bytes. `job_upload.sh`:

    #!/bin/sh
    
    if [ -z "$name" ]; then
        name="stranger"
    fi
    echo "Hello, $name!"
    
    if [ -z "$upload" ]; then
        echo "Looks like you didn't upload a file!"
    else
        FILE_SIZE=$(wc -c $upload | cut -d " " -f1)
        echo "The size in bytes of $upload__name is $FILE_SIZE"
    fi

When we submit the form with a file uploaded, the results look like this:

    Hello, stranger!
    The size in bytes of README.md is 146

Scriptform will stream the uploaded file to a temporary file (usually something
like `/tmp/scriptform_e4CAXk`) and put the received file name in the
`XXXX__name` variable. Temporary files are automatically removed when the
script is done running, so if you want to keep it around, you should move it do
a different directory.

### <a name="tutorial_validation">Validation</a>

Scriptform offers a simple way to validate form values before executing
scripts. This saves you the trouble of having to do all the validation in your
script. Validation is achieved by speciying additional field definition
parameters. 

Let's modify the previous upload example and add some validation to it. We'll
make the `name` field have a minimum and maximum length:

    {
      "name": "name",
      "title": "Name",
      "type": "string",
      "minlen": 2,
      "maxlen": 10
    },

We'll change the `upload` field so it's required and you're only allowed to
upload '.txt' files:


    {
      "name": "upload",
      "title": "Upload a file",
      "type": "file",
      "required": true,
      "extensions": ["txt"]
    }

Try the validation out by submitting the form with some right and wrong values
and by uploading no file or a file with a wrong extension. You'll see that
Scriptform validates the submitted form before the script is executed. If any
validations fail, the form is shown again.

More details on validation and other additional options that can be supplied to
field definitions can be found in the '[Field types](#field_types)' chapter.

### <a name="tutorial_further">Further reading</a>

This concludes the tutorial for Scriptform, although it has a lot more to
offer. Some suggestions on further reading materials:

* [Full user manual](#manual): Everything you need to know.
* [Script execution](#script_execution): Details on how scripts are executed.
* [Users](#users): Scriptform can do user management.
* [Form customization](#cust): Learn how to customize your forms.
* Check the `examples` directory for many interesting examples on how to use
  Scriptform.

And finally, **please read** the [Security](#security) section for important
information regarding Scriptform's security.





## <a name="form_config">Form config (JSON) files</a>

Forms are defined in JSON format. They are referred to as *Form config*
files. A single JSON file may contain multiple forms. Scriptform will show them
on an overview page, and the user can select which form they want to fill out.

Structurally, they are made up of the following elements:

- **`title`**: Text to show at the top of each page. **Required**, **String**.

- **`static_dir`**: Path to a directory from which static files should be
  served. See also "[Serving static files](#output_static_files)".
  **Optional**, **String**.

- **`custom_css`**: Path to a file containing custom CSS. It will be included
  in every page's header. See also "[Form customization](#cust)". **Optional**,
  **String**.

- **`forms`**: A list of dictionaries of form definitions. **Required**, **List
    of dictionaries**.

    - **`name`**: Name for the form. This must be unique. It is used internally
      by Scriptform to refer to forms. **Required**, **String**, **Unique**.

    - **`title`**: Title for the form. This is shown in the list of available
      forms and on the form page itself as the title for the form and as the
      caption for the button which takes you to the form. **Required**,
      **String**.

    - **`description`**: A description of the form. May include HTML tags. This
      is shown in the list of available forms and on the form page itself.
      **Required**, **String**.

    - **`script`**: The path to an executable script of binary that will be
      called if the form is submitted. See also [Callbacks](#callbacks). When
      Scriptform starts, it switches to the directory containing the form
      definition. You should place your scripts there or otherwise specify full
      paths to the scripts.  **Required**, **String**.

    - **`submit_title`**: The text on the submit button of the form.
      **Optional**, **String**, **Default:** `Submit`.

    - **`output`**: Determines how the output of the callback is handled. See
      the [Output](#output) section. The default value is '`escaped`'.
      **Optional**, **String**, **Default:** `escaped`.

    - **`allowed_users`**: A list of users that are allowed to view and submit
      this form. **Optional**, **List of strings**.

    - **`hidden`**: If 'true', don't show the form in the list. You can still
      view it, if you know its name. This is useful for other forms to
      redirect to this forms and such.

    - **`run_as`**: Change to this user (and its groups) before running the
      script. Only works if Scriptform is running as `root`. See also
      [Execution security policy](#script_runas) **Optional**, **String**,
      **Default:** `nobody`.

    - **`fields`**: List of fields in the form. Each field is a dictionary.
      **Required**, **List of dictionaries**.

        - **`name`**: The name of the field. This is what is passed as an
          environment variable to the callback. **Required**, **String**.

        - **`title`**: The title for the field, shown just above the actual
          field. **Required**, **String**.

        - **`type`**: Field type. Supported types are: *string*, *integer*,
          *float*, *date*, *radio*, *checkbox*, *select*, *text*, *password*
          and *file*.  For more information, see [Field types](#field_types).

        - **`required`**: Whether the field is required. **Optional**,
          **Boolean**, **Default:** `false`.

        - **`hidden`**: If 'true', the input field is hidden. This is useful for
          pre-filled forms which takes it values from the GET request.
          **Optional**, **boolean**, **Default:** `false`.

        - **`style`**: A string of inline CSS which will be applied to the field.
          **Optional**, **String**.

        - **`classes`**: A string of optional CSS classes to add to this field.
          **Optional**, **String**.

        - **`...`**: Other options, which depend on the type of field.  For
          more information, see [Field types](#field_types). **Optional**.

- **`users`**: A dictionary of users where the key is the username and the
  value is the plain text password. This field is not required. **Dictionary**.

For example, here's a form config file that contains two forms:

    {
      "title": "Test server",
      "forms": [
          "name": "import",
          "title": "Import data",
          "description": "Import SQL into a database",
          "submit_title": "Import",
          "script": "job_import.sh",
          "fields": [
            {
              "name": "target_db",
              "title": "Database to import to",
              "type": "select",
              "options": [
                ["devtest", "Dev Test db"],
                ["prodtest", "Prod Test db"]
              ]
            },
            {
              "name": "sql_file",
              "title": "SQL file",
              "type": "file"
            }
          ]
        },
        {
          "name": "add_user",
          "title": "Add user",
          "description": "Add a user to the htaccess file or change their password",
          "submit_title": "Add user",
          "script": "job_add_user.sh",
          "fields": [
            {
              "name": "username",
              "title": "Username",
              "type": "string",
              "required": true
            },
            {
              "name": "password1",
              "title": "Password",
              "type": "password",
              "required": true
            },
            {
              "name": "password2",
              "title": "Password (Repear)",
              "type": "password",
              "required": true
            }
          ]
        }
      ]
    }

Many more examples can be found in the `examples` directory in the source code.




## <a name="field_types">Field types</a>

Scriptform supports multiple field types. Field types determine what users may
enter in the field, how they are validated and how they are passed to callback
scripts.

### <a name="field_types_string">String</a>

The `string` field type presents the user with a single line input field.

The `string` field type supports the following additional options:

- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.
- **`size`**: The size (in characters) of the input field.
- **`default_value`**: The default value.

For example:

    ...
    "fields": [
        {
          "name": "my_string",
          "title": "My string",
          "type": "string",
          "minlen": 12,
          "maxlen": 30,
          "size": 30
        }
    ]
    ...

### <a name="field_types_integer">Integer</a>

The `integer` field type presents the user with an input box in which they may
enter an integer number. Depending on the browser's support for HTML5 forms,
the input field may have spin-buttons to increase and decrease the value.

The `integer` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.
- **`default_value`**: The default value.

For example:

    ...
    "fields": [
        {
          "name": "uid",
          "title": "UID",
          "type": "integer",
          "min": 1000,
          "max": 2000
        }
    ]
    ...

### <a name="field_types_float">Float</a>

The `float` field type presents the user with an input box in which they enter
a Real number (fractions).

The `float` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.
- **`default_value`**: The default value.

For example:

    ...
    "fields": [
        {
          "name": "ammount",
          "title": "Ammount",
          "type": "float",
          "min": 10.0,
          "max": 2000.0 
        }
    ]
    ...

Please note that some real numbers cannot be represented exactly by a computer
and validation may thus be approximate. E.g. 0.500000000001 might pass the
test for a maximum value of 0.5. Whether it does depends on the value given,
the platform, your browser, and many other factors.

### <a name="field_types_date">Date</a>

The `date` field type presents the user with an input box in which they can
enter a date. Depending on the browser's support for HTML5 forms, the input
field may have a pop-out calendar from which the user can select a date. 

The date must be entered, and will be passed to the callback, in the form
YYYY-MM-DD.

The `date` field type supports the following additional options:

- **`min`**: The minimum allowed date (format: a string YYYY-MM-DD)
- **`max`**: The maximum allowed date (format: a string YYYY-MM-DD)
- **`default_value`**: The default value.

For example:

    ...
    "fields": [
        {
          "name": "birthdate",
          "title": "Birthdate",
          "type": "date",
          "min": "1900-01-01",
          "max": "2015-01-01"
        }
    ]
    ...

### <a name="field_types_radio">Radio</a>

The `radio` field type lets the user pick one option from a list of options. 

The `radio` field type supports the following additional options:

- **`options`**: The options available to the user. (list of lists, **required**)

For example:

    ...
    "fields": [
        {
            "name": "network",
            "title": "To which network",
            "type": "radio",
            "options": [
                ["intra", "Whole intranet"],
                ["machine", "Acceptance machine"]
            ]
        }
    ]
    ...

### <a name="field_types_checkbox">Checkbox</a>

The `checkbox` field type represents the user with a toggleble checkbox that
can be either 'on' or 'off'.

If the checkbox was checked, the value '`on`' is passed to the script.
Otherwise, '`off`' is passed. Unlike HTML forms, which send no value to the
server if the checkbox was not checked, Scriptform always sends either 'on' or
'off'.

The `checkbox` field type supports the following additional options:

- **`checked`**: Whether the checkbox should be checked by default (boolean)

For example:

    ...
    "fields": [
        {
          "name": "receive_newsletter",
          "title": "Do you want to receive our newsletter?",
          "type": "checkbox",
          "checked": true
        }
    ]
    ...

### <a name="field_types_select">Select</a>

The `select` field presents the user with a dropdown list from which they can
pick a value.

The `select` field type supports the following additional options:

- **`options`**: A list of available options from which the user can choose.
  Each item in the list is itself a list of two values: the value and the
  title.

For example

    ...
    "fields": [
        {
          "name": "source_sql",
          "title": "Load which kind of database?",
          "type": "select",
          "options": [
            ["empty", "Empty database"],
            ["dev", "Development test database"],
            ["ua", "Acceptance database"]
          ]
        }
    ]
    ...


### <a name="field_types_text">Text</a>

The `text` field presents the user with a field in which they can enter
multi-lined text.

The `text` field type supports the following additional options:

- **`rows`**: The number of rows to make the input field
- **`cols`**: The number of cols to make the input filed.
- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.
- **`default_value`**: The default value.

For example:

    ...
    "fields": [
        {
          "name": "complaint",
          "title": "Please write down your complaint",
          "type": "text",
          "rows": 6,
          "cols": 60,
          "minlen": 1,
          "maxlen": 5
        }
    ]
    ...


### <a name="field_types_password">Password</a>

- **`minlen`**: The minimum allowed length for the field.
- **`default_value`**: The default value.

### <a name="field_types_file">File</a>

The `file` field type presents the user with a field through which they can
upload a file. Uploaded files are streamed to temporary files by Scriptform,
after which the original field value is replaced with this temporary file name.
This allows users to upload large files.

The original file name of the uploaded file is stored in a new variable
'&lt;field_name&gt;__name'.

The `file` field type supports the following additional options:

- **`extensions`**: A list of extensions (minus leading dot) that are accepted
  for file uploads. For example: `"extensions": ["csv", "tsv"]`

No additional validation is done on the file contents.

For example:

    ...
    "fields": [
        {
          "name": "new_users",
          "title": "CSV file of new users",
          "type": "file",
          "extensions": ["csv"]
        }
    ]
    ...




## <a name="output">Output</a>

**All output is assumed to be UTF8, regardless of system encoding!**

### <a name="output_types">Output types</a>

Scriptform uses the output of the script (stdout, stderr) to display something
back to the user executing the script.

Scripts can have a few different output types. The output type is specified in
the **`output`** field of the form definition. For example, the following form
definition has a `raw` output type.:

    {
        "name": "display_image",
        "title": "Show an image",
        "description": "Show an image",
        "script: "job_display_image.sh",
        "output": "raw",
        "fields": []
    }

The following output types are supported:

- **`escaped`**: the output of the callback will have its HTML entities escaped
  and will be wrapped in PRE elements. This is the **default** option.

- **`html`**: If the value is `html`, the output will not be escaped or wrapped
  in PRE tags, and can thus include HTML markup. 

- **`raw`**: The output of the script is streamed directly to the client's
  browser. This allows you to output images, binary files, etc to the client.
  The script must include the proper headers and body itself. Examples of raw
  script output can be found in the `examples/raw` directory.


### <a name="output_exitcodes">Exit codes</a>

Exit codes are handled by Scriptform if the output type is not `raw`. Otherwise
it is the script's responsibility to properly handle exit codes of subscripts
and showing errors.

If the output type is `escaped` or `html` and the script's exit code is 0, the
output of the script (stdout) is captured and shown to the user in the browser.

If a script's exit code is not 0, it is assumed an error occured. Scriptform
will show the script's stderr output (in red) to the user instead of stdin.

### <a name="output_static_files">Serving static files</a>

Scriptform can serve static files. It is disabled by default. To enable it,
provide a `static_dir` option in the top section of the form configuration:

    {
        "title": "Static serve",
        "static_dir": "static",
        "forms": [
        ...

This tells Scriptform to serve static files from that location. To refer to a
static file, use the `/static` URL:

    https://example.com/static?fname=foobar.png

Will refer to the `static/foobar.png` file. If `static_dir` is a relative path,
it will be relative to the form configuration (.json) file you're running.

Scriptform does not provide the browser with a content-type of the file, since
it is impossible to guess.  Generally, browsers do a decent job at figuring it
out themselves.

**Note**: Static file serving does not require authentication. All users,
including anonymous users, can view static files.



## <a name="script_execution">Script execution</a>

When the user submits the form, Scriptform will validate the provided values.
If they check out, the specified script for the form will be executed.

A script can be any kind of executable, written in any kind of language,
including scripting languages. As long as it is executable, can read the
environment and output things to stdout it is usable. Scripts written in
scripting languages should include the shebang line that indicates which
interpreter it should use:

    #!/usr/bin/php
    <?php
    echo("Hello!");
    ?>

### <a name="script_validation">Validation</a>

Fields of the form are validated by the Scriptform backend before the script is
called. If you have a HTML5 capable browser, the form will also be validated in
the browser before you submit it.

Exactly what is validated depends on the options specified in the Form
Definition. For more info on that, see the *Field Types* section of this
manual.

Form validation is somewhat limited. For example, you can force a string's
minimum and maximum length, but you cannot do more advanced validation such as
checking if it starts with a certain value. If you wish to do that, you will
have to do the validation in the script callback for a form.

### <a name="script_fieldvalues">Field values</a>

Field values are passed to the script in its environment. For instance, a form
field definition:

    {
      "name": "ip_address",
      "title": "IP Address",
      "type": "string"
    }

becomes available in a shell script as:

    echo $ip_address

or in a Python script as:

    import os
    print os.environ['ip_address']

Uploaded files are streamed to temporary files by Scriptform. The name of the
temporary file is then passed on as the field's value. For example, given the
following field definition:

    {
      "name": "csv_file",
      "title": "CSV file to import",
      "type": "file"
    }

The contents of the file is available in a shell script as:

    echo $csv_file    # output: /tmp/tmp_scriptform_Xu72bK
    ROWS=$(wc -l $csv_file)
    echo "The CSV file has $(expr $ROWS - 1) rows"

These temporary files are automatically cleaned up after the script's execution
ends. 

Examples of file uploads can be found in the `examples/simple` and
`examples/megacorp` directories.

### <a name="script_runas">Execution security policy</a>

Running arbitrary scripts from Scriptform poses somewhat of a security risk.
Scriptform tries to mitigate this risk by running scripts as a different user
in some cases:

* If Scriptform itelf is running as root:
    - By default, scripts will be run as user 'nobody'.
    - If a form specifies as `run_as` field, scripts will be executed as that user.
* If Scriptform itself is running as a non-root user, scripts will be executed
  as that user.

If you use an init script, Scriptform will run as user `root`, which will
cause Scriptform to automatically drop privileges to user `nobody` and group
`nobody` when executing shell scripts. This may cause "permission denied"
problems! There are a few possible ways to work around this:

* Make sure the user or group `nobody` has rights to view and execute the
  scripts. The form configuration itself should probably not be viewable by
  user `nobody` since it may contain passwords.
* Modify the init or systemd script to run as a different user.
* Add `run_as` properties to each form definition to specify the user it
  should run as.



## <a name="users">Users</a>

ScriptForm supports basic htauth user authentication. Users can be defined, and
form access can be limited to certain users. Users are defined in the `users`
top-level field of the form configuration file. For example, in the following
form configuration file, there are two users. Only user `test2` is allowed to
view the form 'only_some_users'.


    {
      "title": "Authorization protected",
      "users": {
        "test": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
        "test2": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
      },
      "forms": [
          "name": "only_some_users",
          "title": "Only some users",
          "description": "You should only see this if you're user 'test2'",
          "submit_title": "Do nothing",
          "script": "job_do_nothing.sh",
          "allowed_users": ["test2"],
          "fields": []
        }
      ]
    }

### <a name="users_passwords">Passwords</a>

Passwords are unsalted SHA256 hashed passwords. To generate one, you can use
the `--generate-pw` option of Scriptform. This will ask you twice for a
plaintext password and return the hash that can be used in the `users` element.

    $ scriptform --generate-pw
    Password: 
    Repeat password: 
    ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
    
**Note** that if you're running from the repository, you'll have to run
Scriptform as:

    $ src/scriptform.py --generate-pw

### <a name="users_formlimit">Form limiting</a>

You may specify a `allowed_users` field in a form definition. Only user names
listed in the field are allowed to see and submit that form. If the user is not
listed, they won't even see the form as being available.

For an example, see the [beginning of this chapter](#users).

### <a name="users_security">Security considerations</a>

- Passwords have no salt. This makes them slightly easier to brute-force en-mass.
- Scriptform does not natively support secure HTTPS connections. This means
  usernames and passwords are transmitted over the line in nearly plain text.
  If you wish to prevent this, you should put Scriptform behind a proxy that
  *does* support HTTPS, such as Apache. For more information on that, see the
  "Invocations" chapter.

### <a name="users_preauth">Pre-authentication with Apache</a>

If you're running behind Apache or another webserver, you can use
features in Apache to do the authentication for you. This allows you to use
LDAP or OpenID (SSO) authentication.

You must pass the `REMOTE_USER` header (not environment variable!) to
Scriptform to get this working. For example, in Apache:

    Redirect permanent /scriptform /scriptform/
    ProxyPass /scriptform/ http://localhost:8081/
    ProxyPassReverse /scriptform/ http://localhost:8081/

    <Location /scriptform>
        AuthType Basic
        AuthName "Restricted Files"
        AuthBasicProvider file
        AuthUserFile "/var/www/users"
        Require valid-user

        Header unset REMOTE_USER
        RequestHeader set REMOTE_USER %{REMOTE_USER}s
    </Location>

If such a header is seen, Scriptform won't perform validation of the password
and just assumes the username is correct.



## <a name="cust">Form customization</a>

### <a name="cust_css">Custom CSS</a>

You can customize a form input field's style using the **`style`** property of
the field definition in the form configuration. It takes a string that will be
put in the generated form's `style=""` HTML attribute. For example:

    "fields": [
        {
            "name": "background",
            "title": "Different background color",
            "type": "string",
            "style": "background-color: #C0FFC0;"
        }
    ]

The example above will render as:

    <input required="" type="text" name="background" value="" size="" class="" style="background-color: #C0FFC0;">

You can also include a global piece of CSS by specifying the **`custom_css`**
property in the form definition. For example:

    {
        "title": "Customized forms",
        "custom_css": "custom.css",
        "forms": [
        ...

`custom.css` is the path to a file which will be included in the rendered HTML
page in the `<style>` header. If the path is relative, it will be relative to
the form configuration file's location.

For a good example, see the `examples/customize/` directory in the source.




## <a name="security">Security</a>

There are a few security issues to take into consideration when deploying Scriptform:

- You should limit harmful forms to specific users. See the [Users](#users)
  chapter for more information.

- User passwords have no salt. This makes them slightly easier to brute-force
  en-mass.

- Scriptform does not natively support secure HTTPS connections. This means
  usernames and passwords are transmitted over the line in nearly plain text.
  If you wish to prevent this, you should put Scriptform behind a proxy that
  *does* support HTTPS, such as Apache. For more information on that, see the
  "Invocations" chapter.

- Scriptform logs the invocation of scripts and variables to the log file for
  auditing purposes. Password values are censored.

- Although Scriptform is written to be secure, it not meant to be served to
  the public internet. **You should only use it in controlled environments
  where a certain level of trust is placed in the users!**. The reason for
  this is because it's really easy to make mistakes in validating input in
  the shell scripts called by Scriptform.

- Although Scriptform validates form fields, it does little to protect against
  things such as shell expansion attacks and such. You should validate your
  input, even (and perhaps most importantly) in shell scripts. If you're
  worried about security, you may want to write your backend scripts in a
  proper language such as Perl or Python.
