#!/usr/bin/python
# ex:set fileencoding=utf-8:

from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.conf import settings
from django import forms
from django import template
from django.template import Library, Node, Variable
from django.template.loader import get_template

register = Library()


class FormNode(Node):
    def __init__(self, template_path, form_as_view):
        self.template_path = template_path
        self.form_as_view = form_as_view

    def render(self, context):
        context.update({'form_as_view': self.form_as_view})
        try:
            t = get_template(self.template_path)
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''
        return t.render(context)


class LayoutNode(Node):
    def __init__(self, obj):
        self.field = Variable(obj)

    def render(self, context):
        field = self.field.resolve(context)
        layout = getattr(field, 'layout', None)

        if hasattr(layout, 'template'):
            template = layout.template
        else:
            template = "djangobmf/forms/layout_field.html"
            if isinstance(field.field.widget, forms.CheckboxInput):
                template = "djangobmf/forms/layout_checkbox.html"
#     if isinstance(field.field.widget, forms.CheckboxSelectMultiple):
#       template = "bmf/forms/layout_checkbox_multiple.html"
#       return '<div>NOT IMPELEMTED</div>'
#     if isinstance(field.field.widget, forms.RadioSelect):
#       template = "bmf/forms/layout_radio.html"
#       return '<div>NOT IMPELEMTED</div>'
            if isinstance(field.field.widget, forms.FileInput):
                template = "djangobmf/forms/layout_file.html"

#   # look for detault templates, if the field does not provide a template information
#   if isinstance(field.field,forms.models.ModelMultipleChoiceField):
#     print field
#     print dir(field.form)
#       print field.field
#       print dir(field.field)
#       return field.form.form_classes[field.name]

        try:
            t = get_template(template)
        except:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''
        return t.render(context)


class HelperNode(Node):
    def __init__(self, as_view):
        self.as_view = Variable(as_view)
        self.form = Variable('form')

    def render(self, context):
        as_view = self.as_view.resolve(context)
        form = self.form.resolve(context)
        return form.bmfhelper.render(form, as_view, context)


@register.tag('bmfhelper')
def bmfhelper(parser, token):
    try:
        tag_name, as_view = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly one argument" % token.contents.split()[0])
    return HelperNode(as_view)


@register.tag('bmfform')
def bmfform(parser, token):
    bits = token.split_contents()
    template = "djangobmf/forms/base_form.html"
    if len(bits) == 2:
        template = bits[1]
    return FormNode(template, form_as_view=False)


@register.tag('bmfview')
def bmfview(parser, token):
    bits = token.split_contents()
    template = "djangobmf/forms/base_view.html"
    if len(bits) == 2:
        template = bits[1]
    return FormNode(template, form_as_view=True)


@register.tag('bmflayout')
def bmflayout(parser, token):
    try:
        tag_name, obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly one argument" % token.contents.split()[0])
    return LayoutNode(obj)


@register.simple_tag
def bmffield(field, only_text):
    # TODO check if you can move this to templates
    if only_text:
        if not hasattr(field.field, 'choices'):
            return '<p class="form-control-static">%s</p>' % field.value()
        if not field.value():
            return '<p class="form-control-static"><i>%s</i></p>' % _('empty')
        if hasattr(field.field.choices, 'queryset'):
            return '<p class="form-control-static">%s</p>' % field.field.choices.queryset.get(pk=field.value())
        else:
            for choice in field.field.choices:
                if choice[0] == field.value():
                    return '<p class="form-control-static">%s</p>' % choice[1]
        return 'NOT IMPLEMENTED in bmfcore/templatetags/djangobmf_form.py'
    else:

        if isinstance(field.field, forms.models.ModelMultipleChoiceField):
            return field.as_widget(attrs={'class': 'form-control'})

        elif isinstance(field.field, forms.models.ModelChoiceField):
            model = field.field.choices.queryset.model
            if hasattr(model, "_bmfmeta"):
                if field.value():
                    # FIXME FAILS IF QUERYSET IS INVALID
                    text = field.field.choices.queryset.get(pk=field.value())
                else:
                    text = None
                if field.field.widget.attrs.get('readonly', False):
                    data = '<p class="form-control-static">%s</p>' % (text or '<i>%s</i>' % _('empty'))
                    data += field.as_hidden(attrs={'autocomplete': 'off'})
                    return data
                else:
                    data = '<div class="input-group" data-bmf-autocomplete="1">'
                    data += field.as_text(attrs={
                        'class': 'form-control',
                        'id': '%s-value' % field.auto_id,
                        'placeholder': text or "",
                        'autocomplete': 'off',
                        'name': '',
                    })
                    data += '</div>'
                    data += field.as_hidden(attrs={'autocomplete': 'off'})
                    return data
            else:
                # TODO: this manages relationsships to non-django models. it makes propably
                # sense to implement a search-function for django models like user
                return field.as_widget(attrs={'class': 'form-control'})

        elif isinstance(field.field, forms.DateTimeField):
            data = '<div class="input-group" data-bmf-calendar="dt">'
            data += field.as_widget(attrs={'class': 'form-control', 'autocomplete': 'off'})
            data += '</div>'
            return data
        elif isinstance(field.field, forms.DateField):
            data = '<div class="input-group" data-bmf-calendar="d">'
            data += field.as_widget(attrs={'class': 'form-control', 'autocomplete': 'off'})
            data += '</div>'
            return data
        elif isinstance(field.field, forms.TimeField):
            data = '<div class="input-group" data-bmf-calendar="t">'
            data += field.as_widget(attrs={'class': 'form-control', 'autocomplete': 'off'})
            data += '</div>'
            return data
        else:
            return field.as_widget(attrs={'class': 'form-control'})
