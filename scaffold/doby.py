def _asdot(value):
    if isinstance(value, list):
        return Loby(value)
    if isinstance(value, tuple):
        return Toby(value)
    if isinstance(value, dict):
        return Doby(value)
    return value


class Toby(tuple):
    def __getitem__(self, item):
        return _asdot(super(Toby, self).__getitem__(item))


class Loby(list):
    def __getitem__(self, item):
        return _asdot(super(Loby, self).__getitem__(item))


class Doby(dict):
    def __getattr__(self, attr):
        return _asdot(self[attr])

    def __getitem__(self, item):
        return _asdot(super(Doby, self).__getitem__(item))
