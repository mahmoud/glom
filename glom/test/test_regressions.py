
def test_frictionless_compat():
    '''
    This was a subtle one involving the frictionless library.
    https://github.com/mahmoud/glom/issues/233
    '''
    class Schema(dict):
        '''minimal stand-in for frictionless.Schema'''
        def __getattr__(self, name):
            if name in self:
                return [self[name]]
            return []

    from glom import glom, Assign

    fields = [
        {"name": "id", "type": "number"},
        {"name": "foo", "type": "datetime"},
        {"name": "bar", "type": "string"},
        {"name": "baz", "type": "boolean"},
    ]
    schema = Schema(fields=fields, missing_values="NA")

    # access
    assert schema.primary_key == []
    assert glom(schema, "primary_key") == []  # fails with KeyError

    # expected
    try:
        assert schema["primaryKey"]
    except KeyError:
        pass

    # expected
    try:
        assert glom(schema, "primaryKey")
    except KeyError:
        pass

    # assign
    glom(schema, Assign("primary_key", "foo"))
    assert schema.primary_key == ["foo"]
    assert schema["primaryKey"] == "foo"

    glom(schema, Assign("primaryKey", "id"))  # fails with AttributeError
    assert schema["primaryKey"] == "id"
