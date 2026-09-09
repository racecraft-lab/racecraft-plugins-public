def simple(x):
    return x + 1


class Box:
    def method(self, a, b):
        if a:
            if b:
                return 1
            return 2
        return 3


def tangled(a, b, c, d, e, f, g, h, i):
    if a and b:
        return 1
    if c or d:
        return 2
    if e:
        return 3
    if f:
        return 4
    if g:
        return 5
    if h:
        return 6
    return i
