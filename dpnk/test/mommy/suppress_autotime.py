# https://stackoverflow.com/a/35943149/2126889

import contextlib

@contextlib.contextmanager
def suppress_autotime(model, fields):
    _original_values = {}
    for field in model._meta.local_fields:
        if field.name in fields:
            _original_values[field.name] = {
                'auto_now': field.auto_now,
                'auto_now_add': field.auto_now_add,
            }
            field.auto_now = False
            field.auto_now_add = False
    try:
        yield
    finally:
        for field in model._meta.local_fields:
            if field.name in fields:
                field.auto_now = _original_values[field.name]['auto_now']
                field.auto_now_add = _original_values[field.name]['auto_now_add']
