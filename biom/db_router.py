class BiomRouter:
    """
    Routes database operations for biom app models to the 'biom' database (MongoDB),
    and all other apps to 'default' (SQLite).
    """

    app_label = 'biom'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:  # noqa: SLF001
            return 'biom'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:  # noqa: SLF001
            return 'biom'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if self.app_label in (obj1._meta.app_label, obj2._meta.app_label):  # noqa: SLF001
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == 'biom'
        return db == 'default'

