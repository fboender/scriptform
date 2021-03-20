"""
FormDefinition holds information about a single form and provides methods for
validation of the form values.
"""

import os
import datetime

import runscript


class ValidationError(Exception):
    """
    Default exception for Validation errors
    """


class FormDefinition(object):
    """
    FormDefinition holds information about a single form and provides methods
    for validation of the form values.
    """
    def __init__(self, name, title, description, fields, script,
                 fields_from=None, default_value=None, output='escaped',
                 hidden=False, submit_title="Submit", allowed_users=None,
                 run_as=None):
        self.name = name
        self.title = title
        self.description = description
        self.fields = fields
        self.script = script
        self.fields_from = fields_from
        self.default_value = default_value
        self.output = output
        self.hidden = hidden
        self.submit_title = submit_title
        self.allowed_users = allowed_users
        self.run_as = run_as

        self.validate_field_defs(self.get_fields())

    def get_fields(self):
        """
        Return the fields for the form either from statically defined fields in
        the form definition, or dynamically from an externally executable
        script.
        """
        if self.fields is not None:
            return self.fields
        elif self.fields_from is not None:
            return runscript.from_file(self.fields_from)
        else:
            msg = "Missing either 'fields' or 'fields_from' in '{}' form"
            raise ValueError(msg.format(self.name))

    def validate_field_defs(self, fields):
        """
        Make sure all required properties are present when loading a field
        definition.
        """
        required = ['name', 'title', 'type']
        for field in fields:
            for prop_name in required:
                if prop_name not in field:
                    raise KeyError("Missing required property '{0}' for field "
                                   "'{1}'".format(prop_name, str(field)))

    def get_field_def(self, field_name):
        """
        Return the field definition for `field_name`.
        """
        for field in self.get_fields():
            if field['name'] == field_name:
                return field
        raise KeyError("Unknown field: {0}".format(field_name))

    def validate(self, form_values):
        """
        Validate all relevant fields for this form against form_values. This
        happens when the form is submitted. Returns a set with the errors and
        new values.
        """
        errors = {}
        values = form_values.copy()

        # First make sure all required fields are there
        for field in self.get_fields():
            field_required = ('required' in field and
                              field['required'] is True)
            field_missing = (field['name'] not in form_values or
                             form_values[field['name']] == '')
            if field_required and field_missing:
                errors.setdefault(field['name'], []).append(
                    "This field is required"
                )

        # Validate the field values, possible casting them to the correct type.
        for field in self.get_fields():
            field_name = field['name']
            if field_name in errors:
                # Skip fields that are required but missing, since they can't
                # be validated
                continue
            try:
                value = self._field_validate(field_name, form_values)
                if value is not None:
                    values[field_name] = value
            except ValidationError as err:
                errors.setdefault(field_name, []).append(str(err))

        return (errors, values)

    def _field_validate(self, field_name, form_values):
        """
        Validate a field in this form. This does a dynamic call to a method on
        this class in the form 'validate_<field_type>'.
        """
        # Find field definition by iterating through all the fields.
        field_def = self.get_field_def(field_name)

        field_type = field_def['type']
        validate_cb = getattr(self, 'validate_{0}'.format(field_type))
        return validate_cb(field_def, form_values)

    def validate_string(self, field_def, form_values):
        """
        Validate a form field of type 'string'.
        """
        value = form_values[field_def['name']]
        maxlen = field_def.get('maxlen', None)
        minlen = field_def.get('minlen', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        if minlen is not None and len(value) < int(minlen):
            raise ValidationError("Minimum length is {0}".format(minlen))
        if maxlen is not None and len(value) > int(maxlen):
            raise ValidationError("Maximum length is {0}".format(maxlen))

        return value

    def validate_integer(self, field_def, form_values):
        """
        Validate a form field of type 'integer'.
        """
        value = form_values[field_def['name']]
        maxval = field_def.get('max', None)
        minval = field_def.get('min', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        try:
            value = int(value)
        except ValueError:
            raise ValidationError("Must be an integer number") from None
        if minval is not None and value < int(minval):
            raise ValidationError("Minimum value is {0}".format(minval))
        if maxval is not None and value > int(maxval):
            raise ValidationError("Maximum value is {0}".format(maxval))

        return int(value)

    def validate_float(self, field_def, form_values):
        """
        Validate a form field of type 'float'.
        """
        value = form_values[field_def['name']]
        maxval = field_def.get('max', None)
        minval = field_def.get('min', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        try:
            value = float(value)
        except ValueError:
            raise ValidationError("Must be an real (float) number") from None
        if minval is not None and value < float(minval):
            raise ValidationError("Minimum value is {0}".format(minval))
        if maxval is not None and value > float(maxval):
            raise ValidationError("Maximum value is {0}".format(maxval))

        return float(value)

    def validate_date(self, field_def, form_values):
        """
        Validate a form field of type 'date'.
        """
        value = form_values[field_def['name']]
        maxval = field_def.get('max', None)
        minval = field_def.get('min', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        try:
            value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            e_msg = "Invalid date, must be in form YYYY-MM-DD"
            raise ValidationError(e_msg) from None

        if minval is not None:
            if value < datetime.datetime.strptime(minval, '%Y-%m-%d').date():
                raise ValidationError("Minimum value is {0}".format(minval))
        if maxval is not None:
            if value > datetime.datetime.strptime(maxval, '%Y-%m-%d').date():
                raise ValidationError("Maximum value is {0}".format(maxval))

        return value

    def validate_radio(self, field_def, form_values):
        """
        Validate a form field of type 'radio'.
        """
        if 'options_from' in field_def:
            # Dynamic options from file
            active_options = runscript.from_file(field_def["options_from"])
        else:
            # Static options defined in form definition
            active_options = field_def['options']

        value = form_values[field_def['name']]
        if value not in [o[0] for o in active_options]:
            raise ValidationError(
                "Invalid value for radio button: {0}".format(value))
        return value

    def validate_select(self, field_def, form_values):
        """
        Validate a form field of type 'select'.
        """
        if 'options_from' in field_def:
            # Dynamic options from file
            active_options = runscript.from_file(field_def["options_from"])
        else:
            # Static options defined in form definition
            active_options = field_def['options']

        value = form_values[field_def['name']]
        if value not in [o[0] for o in active_options]:
            raise ValidationError(
                "Invalid value for dropdown: {0}".format(value))
        return value

    def validate_checkbox(self, field_def, form_values):
        """
        Validate a form field of type 'checkbox'.
        """
        value = form_values.get(field_def['name'], 'off')
        if value not in ['on', 'off']:
            raise ValidationError(
                "Invalid value for checkbox: {0}".format(value))
        return value

    def validate_text(self, field_def, form_values):
        """
        Validate a form field of type 'text'.
        """
        value = form_values[field_def['name']]
        minlen = field_def.get('minlen', None)
        maxlen = field_def.get('maxlen', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        if minlen is not None and len(value) < int(minlen):
            raise ValidationError("Minimum length is {0}".format(minlen))

        if maxlen is not None and len(value) > int(maxlen):
            raise ValidationError("Maximum length is {0}".format(maxlen))

        return value

    def validate_password(self, field_def, form_values):
        """
        Validate a form field of type 'password'.
        """
        value = form_values[field_def['name']]
        minlen = field_def.get('minlen', None)

        if value == '' and field_def.get('required', False) is False:
            return ''
        if minlen is not None and len(value) < int(minlen):
            raise ValidationError("Minimum length is {0}".format(minlen))

        return value

    def validate_file(self, field_def, form_values):
        """
        Validate a form field of type 'file'.
        """
        try:
            value = form_values[field_def['name']]
        except KeyError:
            # Field is missing. Check if it's required.
            if 'required' in field_def and field_def['required'] is True:
                raise ValidationError("Invalid file upload") from None
            else:
                return ''

        field_name = field_def['name']
        upload_fname = form_values[u'{0}__name'.format(field_name)]
        upload_fname_ext = os.path.splitext(upload_fname)[-1].lstrip('.')
        extensions = field_def.get('extensions', None)

        if extensions is not None and upload_fname_ext not in extensions:
            msg = "Only file types allowed: {0}".format(u','.join(extensions))
            raise ValidationError(msg)

        return value
