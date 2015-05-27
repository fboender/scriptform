# Scriptform Manual

This is the manual for version %%VERSION%%.

## Table of Contents

1. [Invocations](#invocations)
    - [Shell foreground](#invocations_foreground)
    - [Daemon](#invocations_daemon)
    - [Init script](#invocations_init)
    - [Behind Apache](#invocations_apache)
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
1. [Users](#users)
    - [Passwords](#users_passwords)
    - [Form limiting](#users_formlimit)
    - [Security considerations](#users_security)
1. [Security](#security)

## <a name="invocations">Invocations</a>

Upon starting Scriptform, it will change the working directory to the path
containing the form definition you've sepcified. It will read the form
definition and perform some basic sanity checks to see if, for instance, the
scripts you specified exist and are executable.

There are multiple ways of running ScriptForm. This chapter outlines the
various methods. They are listed in the order of least to most
pruduction-ready.

### <a name="invocations_foreground">Shell foreground</a>

Sriptform can be run directly from the shell in the foreground with the `-f`
(`--foreground`) option. This is most useful for testing and development:

    $ /usr/bin/scriptform -p8000 -f ./formdef.json

### <a name="invocations_daemon">Daemon</a>

If you do not specify the `-f` option, Scriptform will go into the background:

    $ /usr/bin/scriptform -p8000 ./formdef.json
    $

A pid file will be written in the current directory, or to the file specified
by `--pid-file`. A log file will be written a .log file in the current
directory, or to the file specified by the `--log-file` option.

To stop the daemon, invoke the command with the `--stop` option. You must
specifiy at least the `--pid-file` option, if the daemon was started with one.

    $ /usr/bin/scriptform --pid-file /var/run/scriptform.pid --stop

### <a name="invocations_init">Init script</a>

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

### <a name="invocations_apache">Behind Apache</a>

Enable Apache modules mod_proxy and mod_proxy_http:

    $ sudo a2enmod proxy
    $ sudo a2enmod proxy_http

Configure:

    Redirect permanent /scriptform /scriptform/
    ProxyPass /scriptform/ http://localhost:8000/
    ProxyPassReverse /scriptform/ http://localhost:8000/

Make sure the path ends in a slash! (That's what the redirect is for).
Otherwise, you may encounter the following error:

    +  TypeError: index() got an unexpected keyword argument 'form_name'

## <a name="form_config">Form config (JSON) files</a>

Forms are defined in JSON format. They are referred to as *Form config*
files. A single JSON file may contain multiple forms. Scriptform will show them
on an overview page, and the user can select which form they want to fill out.

Structurally, they are made up of the following elements:

- **`title`**: Text to show at the top of each page. **Required**, **String**.

- **`static_dir`**: Path to a directory from which static files should be
  served. See also "[Serving static files](#output_static_files)".
  **Optional**, **String**.

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

    - **`style`**: A string of inline CSS which will be applied to the field.
      **Optional**, **String**.

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

        - **`...`**: Other options, which depend on the type of field.  For
          more information, see [Field types](#field_types). **Optional**.

- **`users`**: A dictionary of users where the key is the username and the
  value is the plaintext password. This field is not required. **Dictionary**.

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
              "type": "string"
            },
            {
              "name": "password1",
              "title": "Password",
              "type": "password"
            },
            {
              "name": "password2",
              "title": "Password (Repear)",
              "type": "password"
            }
          ]
        }
      ]
    }

Many more examples can be found in the `examples` directory in the source code.

## <a name="field_types">Field types</a>

### <a name="field_types_string">String</a>

The `string` field type presents the user with a single line input field.

The `string` field type supports the following additional options:

- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.
- **`size`**: The size (in characters) of the input field.

### <a name="field_types_integer">Integer</a>

The `integer` field type presents the user with an input box in wich they may
enter an integer number. Depending on the browser's support for HTML5 forms,
the input field may have spin-buttons to increase and decrease the value.

The `integer` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.

### <a name="field_types_float">Float</a>

The `float` field type presents the user with an input box in which they enter
a Real number (fractions).

The `float` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.

Please note that some real numbers cannot be represented exactly by a computer
and validation may thus be approximate. E.g. 0.499999999999999 will pass the
test for a maximum value of 0.5.

### <a name="field_types_date">Date</a>

The `date` field type presents the user with an input box in which they can
enter a date. Depending on the browser's support for HTML5 forms, the input
field may have a pop-out calendar from which the user can select a date. 

The date must be entered, and will be passed to the callback, in the form
YYYY-MM-DD.

The `date` field type supports the following additional options:

- **`min`**: The minimum allowed date (format: a string YYYY-MM-DD)
- **`max`**: The maximum allowed date (format: a string YYYY-MM-DD)

### <a name="field_types_radio">Radio</a>

### <a name="field_types_checkbox">Checkbox</a>

The `checkbox` field type represents the user with a toggleble checkbox that
can be either 'on' or 'off'.

If the checkbox was checked, the value '`on`' is passed to the script.
Otherwise, '`off`' is passed. Unlike HTML forms, which send no value to the
server if the checkbox was not checked, Scriptform always sends either 'on' or
'off'.

### <a name="field_types_select">Select</a>

### <a name="field_types_text">Text</a>

The `text` field presents the user with a field in which they can enter
multi-lined text.

The `text` field type supports the following additional options:

- **`rows`**: The number of rows to make the input field
- **`cols`**: The number of cols to make the input filed.
- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.

### <a name="field_types_password">Password</a>

- **`minlen`**: The minimum allowed length for the field.

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

No additional validatikon is done on the file contents.

## <a name="output">Output</a>

**All output is assumed to be UTF8, regardless of system encoding!**

### <a name="output_types">Output types</a>

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

If the script's exit code is 0, the output of the script (stdout) is captured
and shown to the user in the browser.

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

## <a name="script_executing">Script execution</a>

When the user submits the form, scriptform will validate the provided values.
If they check out, the specified script for the form will be executed.

A script can be any kind of executable, written in any kind of language,
including scripting languages. As long as it is executable, can read the
environment and output things to stdout it is usable. Scippts written in
scripting languages should include the shebang line that indicates which
interpreter it should use:

    #!/usr/bin/php
    <?php
    echo("Hello!");
    ?>

### <a name="script_validation">Validation</a>

Fields of the form are validated by Scriptform before the script is called.
Exactly what is validated depends on the options specified in the Form
Definition. For more info on that, see the *Field Types* section of this
manual.

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

These temporary files are automatically cleaned up after the script's exeuction
ends. 

Examples of file uploads can be found in the `examples/simple` and
`examples/megacorp` directories.


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

    $ ./scriptform.py --generate-pw
    Password: 
    Repeat password: 
    ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
    
### <a name="users_formlimit">Form limiting</a>

You may specify a `allowed_users` field in a form definition. Only user names
listed in the field are allowed to see and submit that form. If the user is not
listed, they won't even see the form as being available.

For an example, see the (beginning of this chapter)[#users].

### <a name="users_security">Security considerations</a>

- Passwords have no salt. This makes them slightly easier to bruteforce en-mass.
- Scriptform does not natively support secure HTTPS connections. This means
  usernames and passwords are transmitted over the line in nearly plaintext. If
  you wish to prevent this, you should put Scriptform behind a proxy that
  *does* support HTTPS, such as Apache. For more information on that, see
  the "Invocations" chapter.

## <a name="security">Security</a>

There are a few security issues to take into consideration when deploying Scriptform:

- You should limit harmful forms to specific users. See the [Users](#users)
  chapter for more information.

- User passwords have no salt. This makes them slightly easier to bruteforce
  en-mass.

- Scriptform does not natively support secure HTTPS connections. This means
  usernames and passwords are transmitted over the line in nearly plaintext. If
  you wish to prevent this, you should put Scriptform behind a proxy that
  *does* support HTTPS, such as Apache. For more information on that, see
  the "Invocations" chapter.

- Scriptform logs the invocation of scripts and variables to the log file for
  auditing purposes.

- Scriptform is not meant to be served to the public internet. **You should
  only use it in controlled environments where a certain level of trust is
  placed in the users!**
