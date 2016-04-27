def asdot(value):
    if isinstance(value, list):
        return Loty(value)
    if isinstance(value, tuple):
        return Toty(value)
    if isinstance(value, dict):
        return Doty(value)
    return value

class Toty(tuple):
    def __getitem__(self, item):
        return asdot(super(Toty, self).__getitem__(item))

class Loty(list):
    def __getitem__(self, item):
        return asdot(super(Loty, self).__getitem__(item))

class Doty(dict):
    def __getattr__(self, attr):
        return asdot(self[attr])

    def __getitem__(self, item):
        return asdot(super(Doty, self).__getitem__(item))

    # __setattr__ could raise exception, since Doty is meant to be read-only
    # __setitem__ could raise exception, since Doty is meant to be read-only

    
thingd = { 'one': 'a',
           'Two': 'b',
           'three': 'c',
           'four': 'd',
           'mega': [
               'first',
               { 'foo': 'bar',
                 'baz': 'qux',
                 }
               ],
           'giga': {
               'a':1,
               'b':2,
               'c':3
               }
           }

thingy = Doty(thingd)

print thingy.one
print thingy['Two']
print thingy.Two
print thingy.three
print thingy['four']

print thingy.mega[0]
print thingy.mega[1].baz
print thingy.giga.b
print thingy['giga'].a
