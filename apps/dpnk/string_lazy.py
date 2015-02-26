from django.utils import six  # Python 3 compatibility
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
mark_safe_lazy = lazy(mark_safe, six.text_type)

def format_lazy(string, *args, **kwargs):
    return string.format(*args, **kwargs)
format_lazy = lazy(format_lazy, unicode)
