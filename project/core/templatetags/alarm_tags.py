from django import template

register = template.Library()

@register.filter
def getattr_field(obj, field_name):
    # return the dinamic value of the obj
    # used in the manual.html to change the language shown in the table
    return getattr(obj, field_name, "")
