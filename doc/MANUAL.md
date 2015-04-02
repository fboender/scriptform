# Scriptform Manual

## Table of Contents

1. Invocations
1. [Form definition (JSON) files](#form_def)
1. [Field types](#form_def)
    - [String](#form_def)
    - [Integer](#form_def)
    - [Float](#form_def)
    - [Date](#form_def)
    - [Radio](#form_def)
    - [Select](#form_def)
    - [Text](#form_def)
    - [Password](#form_def)
    - [File](#form_def)
1. [Output](#output)
1. [Callbacks](#form_def)
    - [Script callbacks]()
        - [Validation]()
        - [Field Values]()
    - [Python callbacks]()
1. [Users](#users)

## Invocations

### Behind Apache

Enable Apache modules mod_proxy and mod_proxy_http:

    $ sudo a2enmod proxy
    $ sudo a2enmod proxy_http

Configure:

    Redirect permanent /scriptform /scriptform/
    ProxyPass /scriptform/ http://localhost:8000/
    ProxyPassReverse /scriptform/ http://localhost:8000/

Make sure the path ends in a slash! (That's what the redirect is for).

## Form config (JSON) files

Forms are defined in JSON format. They are referred to as *Form config*
files. A single JSON file may contain multiple forms. Scriptform will show them
on an overview page, and the user can select which form they want to fill out.

Structurally, they are made up of the following elements:

- **`title`**: Text to show at the top of each page. **Required**, **String**.
- **`forms`**: Dictionary where the key is the form id and the value is a
  dictionary that is the definition for a single form. **Required**, **Dictionary**.
    - **`title`**: Title for the form. **Required**, **String**.
    - **`description`**: A description of the form. May include HTML tags. **Required**, **String**.
    - **`submit_title`**: The text on the submit button of the form.
    - **`script`**: The path to an executable script of binary that will be
      called if the form is submitted. See also [[Callbacks]]. If this field is
      omitted, Scriptform will instead call a python callable (function,
      method) that's been registered. Scriptform will raise an error if the
      script isn't found, if the script isn't executable or (if the `script`
      tag is omitted) if no Python callback is registered to handle this form.
      **String**.
    - **`output`**: Determines how the output of the callback is handled. See
      the *Output types* seciton.
    - **`fields`**: List of fields in the form. Each field is a dictionary.
      **Required**, **List of dictionaries**.
        - **`name`**: The name of the field. This is what is passed as an
          environment variable to the callback.
        - **`title`**: The title for the field, shown just above the actual
          field.
        - **`type`**: Field type. Supported types are: *string*, *integer*,
          *float*, *date*, *radio*, *select*, *text*, *password* and *file*.
          For more information, see [Field types].
        - **`required`**: Whether the field is required.
        - **`...`**: Other options, which depend on the type of field.
- **`users`**: A dictionary of users where the key is the username and the
  value is the plaintext password. This field is not required. **Dictionary**.

For example, here's a form config file that contains two forms:

    {
      "title": "Test server",
      "forms": {
        "import": {
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
        "add_user": {
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
      }
    }


## Field types

### String

The `string` field type presents the user with a single line input field.

The `string` field type supports the following additional options:

- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.

### Integer

The `integer` field type presents the user with an input box in wich they may
enter an integer number. Depending on the browser's support for HTML5 forms,
the input field may have spin-buttons to increase and decrease the value.

The `integer` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.

### Float

The `float` field type presents the user with an input box in which they enter
a Real number (fractions).

The `float` field type supports the following additional options:

- **`min`**: The minimum allowed value for the field.
- **`max`**: The maximum allowed value for the field.

Please note that some real numbers cannot be represented exactly by a computer
and validation may thus be approximate. E.g. 0.499999999999999 will pass the
test for a maximum value of 0.5.

### Date

The `date` field type presents the user with an input box in which they can
enter a date. Depending on the browser's support for HTML5 forms, the input
field may have a pop-out calendar from which the user can select a date. 

The date must be entered, and will be passed to the callback, in the form
YYYY-MM-DD.

The `date` field type supports the following additional options:

- **`min`**: The minimum allowed date (format: a string YYYY-MM-DD)
- **`max`**: The maximum allowed date (format: a string YYYY-MM-DD)

### Radio

### Select

### Text

The `text` field presents the user with a field in which they can enter
multi-lined text.

The `text` field type supports the following additional options:

- **`rows`**: The number of rows to make the input field
- **`cols`**: The number of cols to make the input filed.
- **`minlen`**: The minimum allowed length for the field.
- **`maxlen`**: The maximum allowed length for the field.

### Password

- **`minlen`**: The minimum allowed length for the field.

### File

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

FIXME

      If
      its value is `escaped`, the output of the callback will have its HTML
      entities escaped and will be wrapped in PRE elements. This is the
      **default** option. If the value is `html`, the output will not be
      escaped or wrapped in PRE tags, and can thus include HTML markup. If the
      output is `raw`, the output of the script is streamed directly to the
      client's browser. This allows you to output images, binary files, etc to
      the client. The script must include the proper headers and body itself. 

If the script's exit code is 0, the output of the script (stdout) is captured
and shown to the user in the browser.

If a script's exit code is not 0, it is assumed an error occured. Scriptform
will show the script's stderr output (in red) to the user instead of stdin.

FIXME:
If the form definition has a `script_raw` field, and its value is `true`,
Scriptform will pass the output of the script to the browser as-is. This allows
scripts to show images, stream a file download to the browser or even show
completely custom HTML output. The script's output must be a valid HTTP
response, including headers and a body. Examples of raw script output can be
found in the `examples/raw` directory.

## Callbacks

Callbacks are called after the form has been submitted and its values have been
validated. They are the actual implementations of the form's action.

There are two types of callbacks:

- Scripts
- Python callables (functions or methods)

### Scripts

A script callback can be any kind of executable, written in any kind of
language. As long as it is executable, can read the environment and output
things to stdout, it can be used as a callback.

#### Validation

Fields of the form are validated by Scriptform before the script is called.
Exactly what is validated depends on the options specified in the Form
Definition. For more info on that, see the *Field Types* section of this
manual.

#### Field values

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


### Python callbacks

## <a name="users">Users</a>

