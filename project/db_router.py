"""DB router"""

from dpnk.models import Payment


class ReadWriteDbRouter:
    """Read write operations DB router"""

    def db_for_read(self, model, **hints):
        if model is Payment:
            return "default"
        return "read_replica"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
