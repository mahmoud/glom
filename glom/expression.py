import glom


class F(object):
    """
    F for filter expression!
    An F object encapsulates boolean comparisons in a similar
    manner to SQLAlchemy or Pandas columns.
    Given a sequence of objects that you want to filter.
    [Check(F(T.a) == 3 & F(T.b) > 3), default=glom.SKIP]
    """
    def __init__(self, spec, op=None, rhs=None):
        self.spec, self.op, self.rhs = spec, op, rhs

    def __eq__(self, other):
        return F(self, lambda a, b: a == b, other)

    def __and__(self, other):
        return F(self, lambda a, b: a and b, other)

    def __or__(self, other):
        return F(self, lambda a, b: a or b, other)

    def __gt__(self, other):
        return F(self, lambda a, b: a > b, other)

    def __lt__(self, other):
        return F(self, lambda a, b: a < b, other)

    def glomit(self, target, scope):
        # TODO: this evaluation could be made a lot faster
        # by avoiding recursion except at the leaf specs
        lhs = scope[glom.glom](target, self.spec, scope)
        if self.op is None and self.rhs is None:
            return lhs
        rhs = scope[glom.glom](target, self.rhs, scope)
        return self.op(lhs, rhs)
