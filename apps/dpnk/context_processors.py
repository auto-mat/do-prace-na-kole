from django.conf import settings # import the settings file

def settings_properties(request):
    return {'HEADER_COLOR': getattr(settings, 'HEADER_COLOR', "")}
