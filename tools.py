"""

"""

## python imports

from functools import wraps

## __all__ declaration

__all__ = (
    "classproperty",
)

## classproperty declaration

class classproperty(property):
    """A descriptor for a class rather than an object/instance. Used by
    decorating an class method with no parameters. Acting similarly to the
    property descriptor builtin and uses `functools.wraps` to maintain
    documentation.
    """

    def __new__(cls, fget=None, doc=None, lazy=False):
        if fget is None:
            def wrapper(func):
                return cls(func, lazy=lazy)

            return wrapper

        return super().__new__(cls)

    def __init__(self, fget, doc=None, lazy=False):
        self._lazy = lazy
        if lazy:
            self._cache = {}
        fget = self._wrap_fget(fget)

        super().__init__(fget=fget, doc=doc)

    def __get__(self, obj, objtype):
        if self._lazy and objtype in self._cache:
            return self._cache[objtype]

        val = self.fget.__wrapped__(objtype)

        if self._lazy:
            self._cache[objtype] = val

        return val

    def getter(self, fget):
        return super().getter(self._wrap_fget(fget))

    @staticmethod
    def _wrap_fget(orig_fget):
        if isinstance(orig_fget, classmethod):
            orig_fget = orig_fget.__func__

        @wraps(orig_fget)
        def fget(obj):
            return orig_fget(obj.__class__)

        return fget