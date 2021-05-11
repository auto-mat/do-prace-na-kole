from model_mommy import mommy


class Mom:
    def __init__(self, *args, **kwargs):
        self.o = mommy.make(*args, **kwargs)

    def __enter__(self):
        return self.o

    def __exit__(self, exc_type, exc_value, tb):
        self.o.delete()
