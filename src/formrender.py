html_field = u'''
  <li class="{classes}">
    <p class="form-field-title">{title}</p>
    <p class="form-field-input">{input} <span class="error">{errors}</span></p>
  </li>
'''

html_field_checkbox = u'''
  <li class="checkbox {classes}">
    <p class="form-field-input">{input} <p class="form-field-title">{title}</p><span class="error">{errors}</span></p>
  </li>
'''


class FormRender():
    field_tpl = {
        "string": u'<input {required} type="text" name="{name}" value="{value}" size="{size}" class="{classes}" style="{style}" />',
        "number": u'<input {required} type="number" min="{min}" max="{max}" name="{name}" value="{value}" class="{classes}" style="{style}" />',
        "integer": u'<input {required} type="number" min="{min}" max="{max}" name="{name}" value="{value}" class="{classes}" style="{style}" />',
        "float": u'<input {required} type="number" min="{min}" max="{max}" step="any" name="{name}" value="{value}" class="{classes}" style="{style}" />',
        "date": u'<input {required} type="date" name="{name}" value="{value}" class="{classes}" style="{style}" />',
        "file": u'<input {required} type="file" name="{name}" class="{classes}" style="{style}" />',
        "password": u'<input {required} type="password" min="{min}" name="{name}" value="{value}" class="{classes}" style="{style}" />',
        "text": u'<textarea {required} name="{name}" rows="{rows}" cols="{cols}" style="{style}" class="{classes}">{value}</textarea>',
        "radio_option": u'<input {checked} type="radio" name="{name}" value="{value}" class="{classes} style="{style}"">{label}<br/>',
        "select_option": u'<option value="{value}" style="{style}" {selected}>{label}</option>',
        "select": u'<select name="{name}" class="{classes}" style="{style}">{select_elems}</select>',
        "checkbox": u'<input {checked} type="checkbox" name="{name}" value="on" class="{classes} style="{style}"" />',
    }

    def __init__(self, form_def):
        self.form_def = form_def

    def cast_params(self, params):
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

    def r_field(self, type, **kwargs):
        params = self.cast_params(kwargs)
        method_name = 'r_field_{0}'.format(type)
        method = getattr(self, method_name, None)
        return method(**params)

    def r_field_string(self, name, value, size=50, required=False, classes=[], style=""):
        tpl = self.field_tpl['string']
        return tpl.format(name=name, value=value, size=size, required=required, classes=classes, style=style)

    def r_field_number(self, name, value, min=None, max=None, required=False, classes=[], style=""):
        tpl = self.field_tpl['number']
        return tpl.format(name=name, value=value, min=min, max=max, required=required, classes=classes, style=style)

    def r_field_integer(self, name, value, min=None, max=None, required=False, classes=[], style=""):
        tpl = self.field_tpl['integer']
        return tpl.format(name=name, value=value, min=min, max=max, required=required, classes=classes, style=style)

    def r_field_float(self, name, value, min=None, max=None, required=False, classes=[], style=""):
        tpl = self.field_tpl['integer']
        return tpl.format(name=name, value=value, min=min, max=max, required=required, classes=classes, style=style)

    def r_field_date(self, name, value, required=False, classes=[], style=""):
        tpl = self.field_tpl['date']
        return tpl.format(name=name, value=value, required=required, classes=classes, style=style)

    def r_field_file(self, name, required=False, classes=[], style=""):
        tpl = self.field_tpl['file']
        return tpl.format(name=name, required=required, classes=classes, style=style)

    def r_field_password(self, name, value, min=None, required=False, classes=[], style=""):
        tpl = self.field_tpl['password']
        return tpl.format(name=name, value=value, min=min, required=required, classes=classes, style=style)

    def r_field_text(self, name, value, rows=4, cols=80, required=False, classes=[], style=""):
        tpl = self.field_tpl['text']
        return tpl.format(name=name, value=value, rows=rows, cols=cols, required=required, classes=classes, style=style)

    def r_field_radio(self, name, value, options, classes=[], style=""):
        tpl_option = self.field_tpl['radio_option']
        radio_elems = []
        for o_value, o_label in options:
            checked = ''
            if o_value == value:
                checked = 'checked'
            radio_elems.append(tpl_option.format(name=name, value=value, checked=checked, label=o_label, classes=classes, style=style))
        return u''.join(radio_elems)

    def r_field_checkbox(self, name, checked, classes='', style=""):
        tpl = self.field_tpl['checkbox']
        return tpl.format(name=name, checked=checked, classes=classes, style=style)

    def r_field_select(self, name, value, options, classes=[], style=""):
        tpl_option = self.field_tpl['select_option']
        select_elems = []
        for o_value, o_label in options:
            selected = ''
            if o_value == value:
                selected = 'selected'
            select_elems.append(tpl_option.format(value=o_value, selected=selected, label=o_label, style=style))

        tpl = self.field_tpl['select']
        return tpl.format(name=name, select_elems=''.join(select_elems), classes=classes, style=style)

    def r_form_line(self, type, title, input, classes, errors):
        if type == 'checkbox':
            html = html_field_checkbox
        else:
            html = html_field

        return (html.format(classes=' '.join(classes),
                            title=title,
                            input=input,
                            errors=u', '.join(errors)))
