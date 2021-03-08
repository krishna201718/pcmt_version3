from django import template
from ..models import Subject

register = template.Library()


@register.filter
def index( indexable, i):
    try:
        return indexable[i]
    except:
        return 0


@register.filter
def get_subject(subject_Id):
    obj = Subject.object.get(subject=subject_Id)
    return obj.name


@register.filter
def times(number):
    return range(1,number)