"""Serializing Django forms for a JS front end that renders them itself."""


def get_form_json(form):
    """Serialize a Django form as a field schema plus current values.

    The consumer is a JS component that renders the fields itself (see DjangoForm.jsx), so this
    carries the type/widget/choices metadata it needs, not just the values.
    """
    form_json = {
        'fields': [],
        'data': {},
    }
    for name, field in form.fields.items():
        field_class = get_class_str(field)
        field_info = {
            'name': name,
            'id': 'id_' + name,
            'type': field_class,
            'label': field.label,
            'initial': form.initial[name],
            'error_messages': field.error_messages,
            'required': field.required,
        }
        form_json['data'][name] = form.initial[name]
        choices = getattr(field, 'choices', None)
        max_length = getattr(field, 'max_length', None)
        min_length = getattr(field, 'min_length', None)
        if choices: field_info['choices'] = choices
        if max_length: field_info['max_length'] = max_length
        if min_length: field_info['min_length'] = min_length
        widget = getattr(field, 'widget', None)
        if widget:
            attrs = getattr(widget, 'attrs', None)
            field_info['widget'] = get_class_str(widget)
            if attrs: field_info['widget_attrs'] = attrs
        form_json['fields'].append(field_info)
    return form_json


def get_class_str(o):
    return str(type(o)).replace("<class '", "").replace("'>", "")
