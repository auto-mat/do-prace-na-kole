#!/usr/bin/python
import os
import sys

# BEGIN activacte virtualenv
from project.settings import PROJECT_ROOT, normpath

try:
    activate_path = normpath(PROJECT_ROOT, 'env/bin/activate_this.py')
    execfile(activate_path, dict(__file__=activate_path))
except IOError:
    print "E: virtualenv must be installed to PROJECT_ROOT/env"
# END activacte virtualenv

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
