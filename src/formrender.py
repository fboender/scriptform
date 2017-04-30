# -*- coding: utf8 -*-

"""
FormRender takes care of the rendering of forms to HTML.
"""

HTML_FIELD = u'''
  <li class="{classes}">
    <p class="form-field-title">{title}</p>
    <p class="form-field-input">
      {h_input}
      <span class="error">{errors}</span>
    </p>
  </li>
'''

HTML_FIELD_CHECKBOX = u'''
  <li class="checkbox {classes}">
    <p class="form-field-input">
      {h_input}
      <p class="form-field-title">{title}</p>
      <span class="error">{errors}</span>
    </p>
  </li>
'''

HTML_REQUIRED = u'{0} <abbr title="This field is required" \
                u"class="required">•</span>'


class FormRender(object):
    """
    FormRender takes care of the rendering of forms to HTML.
    """
    field_tpl = {
        "string": u'<input {required} type="text" name="{name}" '
                  u'value="{value}" size="{size}" '
                  u'class="{classes}" style="{style}" minlength="{minlen}" '
                  u' maxlength="{maxlen}" />',
        "integer": u'<input {required} type="number" min="{minval}" '
                   u'max="{maxval}" name="{name}" value="{value}" '
                   u'class="{classes}" style="{style}" />',
        "float": u'<input {required} type="number" min="{minval}" '
                 u'max="{maxval}" step="any" name="{name}" '
                 u'value="{value}" class="{classes}" style="{style}" />',
        "date": u'<input {required} type="date" name="{name}" value="{value}" '
                u'min="{minval}" max="{maxval}" class="{classes}" '
                u'style="{style}" />',
        "file": u'<input {required} type="file" name="{name}" '
                u'class="{classes}" style="{style}" />',
        "password": u'<input {required} type="password" minlength="{minlen}" '
                    u'name="{name}" value="{value}" class="{classes}" '
                    u'style="{style}" />',
        "text": u'<textarea {required} name="{name}" rows="{rows}" '
                u'cols="{cols}" minlength="{minlen}" maxlength="{maxlen}" '
                u'style="{style}" class="{classes}">{value}</textarea>',
        "radio_option": u'<input {checked} type="radio" name="{name}" '
                        u'value="{value}" class="{classes}" '
                        u'style="{style}">{label}<br/>',
        "select_option": u'<option value="{value}" style="{style}" '
                         u'{selected}>{label}</option>',
        "select": u'<select name="{name}" class="{classes}" '
                  u'style="{style}">{select_elems}</select>',
        "checkbox": u'<input {checked} type="checkbox" name="{name}" '
                    u'value="on" class="{classes}" style="{style}" />',
    }

    def __init__(self, form_def):
        self.form_def = form_def

    def cast_params(self, params):
        """
        Casts values in `params` dictionary to the correct types and values for
        use in the form rendering.
        """
        new_params = params.copy()

        if 'required' in new_params:
            if new_params['required'] is False:
                new_params['required'] = ""
            else:
                new_params["required"] = "required"

        if 'classes' in new_params:
            new_params['classes'] = ' '.join(new_params['classes'])

        if 'checked' in new_params:
            if new_params['checked'] is False:
                new_params['checked'] = ""
            else:
                new_params['checked'] = "checked"

        return new_params

    def r_field(self, field_type, **kwargs):
        """
        Render a generic field to HTML.
        """
        params = self.cast_params(kwargs)
        method_name = 'r_field_{0}'.format(field_type)
        method = getattr(self, method_name, None)
        field = method(**params)

        if 'required' in kwargs and kwargs['required'] is True:
            return HTML_REQUIRED.format(field)
        else:
            return field

    def r_field_string(self, name, value, minlen=None, maxlen=None, size=50,
                       required=False, classes='', style=""):
        """
        Render a string field to HTML.
        """
        tpl = self.field_tpl['string']
        return tpl.format(name=name, value=value, minlen=minlen, maxlen=maxlen,
                          size=size, required=required, classes=classes,
                          style=style)

    def r_field_integer(self, name, value, minval=None, maxval=None,
                        required=False, classes='', style=""):
        """
        Render a integer field to HTML.
        """
        tpl = self.field_tpl['integer']
        return tpl.format(name=name, value=value, minval=minval, maxval=maxval,
                          required=required, classes=classes, style=style)

    def r_field_float(self, name, value, minval=None, maxval=None,
                      required=False, classes='', style=""):
        """
        Render a float field to HTML.
        """
        tpl = self.field_tpl['float']
        return tpl.format(name=name, value=value, minval=minval, maxval=maxval,
                          required=required, classes=classes, style=style)

    def r_field_date(self, name, value, minval='', maxval='', required=False,
                     classes='', style=""):
        """
        Render a date field to HTML.
        """
        tpl = self.field_tpl['date']
        return tpl.format(name=name, value=value, minval=minval, maxval=maxval,
                          required=required, classes=classes, style=style)

    def r_field_file(self, name, required=False, classes='', style=""):
        """
        Render a file field to HTML.
        """
        tpl = self.field_tpl['file']
        return tpl.format(name=name, required=required, classes=classes,
                          style=style)

    def r_field_password(self, name, value, minlen=None, required=False,
                         classes='', style=""):
        """
        Render a password field to HTML.
        """
        tpl = self.field_tpl['password']
        return tpl.format(name=name, value=value, minlen=minlen,
                          required=required, classes=classes, style=style)

    def r_field_text(self, name, value, rows=4, cols=80, minlen=None,
                     maxlen=None, required=False, classes='', style=""):
        """
        Render a text field to HTML.
        """
        tpl = self.field_tpl['text']
        return tpl.format(name=name, value=value, rows=rows, cols=cols,
                          minlen=minlen, maxlen=maxlen, required=required,
                          classes=classes, style=style)

    def r_field_radio(self, name, value, options, classes='', style=""):
        """
        Render a radio field to HTML.
        """
        tpl_option = self.field_tpl['radio_option']
        radio_elems = []
        for o_value, o_label in options:
            checked = ''
            if o_value == value:
                checked = 'checked'
            radio_elems.append(tpl_option.format(name=name,
                                                 value=value,
                                                 checked=checked,
                                                 label=o_label,
                                                 classes=classes,
                                                 style=style))
        return u''.join(radio_elems)

    def r_field_checkbox(self, name, checked, classes='', style=""):
        """
        Render a checkbox field to HTML.
        """
        tpl = self.field_tpl['checkbox']
        return tpl.format(name=name, checked=checked, classes=classes,
                          style=style)

    def r_field_select(self, name, value, options, classes='', style=""):
        """
        Render a select field to HTML.
        """
        tpl_option = self.field_tpl['select_option']
        select_elems = []
        for o_value, o_label in options:
            selected = ''
            if o_value == value:
                selected = 'selected'
            select_elems.append(tpl_option.format(value=o_value,
                                                  selected=selected,
                                                  label=o_label,
                                                  style=style))

        tpl = self.field_tpl['select']
        return tpl.format(name=name, select_elems=''.join(select_elems),
                          classes=classes, style=style)

    def r_form_line(self, field_type, title, h_input, classes, errors):
        """
        Render a line (label + input) to HTML.
        """
        if field_type == 'checkbox':
            html = HTML_FIELD_CHECKBOX
        else:
            html = HTML_FIELD

        return (html.format(classes=' '.join(classes),
                            title=title,
                            h_input=h_input,
                            errors=u', '.join(errors)))
