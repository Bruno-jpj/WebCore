from django import template

register = template.Library()

@register.filter
def getattr_field(obj, field_name):
    """Restituisce il valore del campo dinamico dell'oggetto."""
    return getattr(obj, field_name, "")
