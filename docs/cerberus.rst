``glom.Match`` compared with ``Cerberus``
=========================================

Comparing glom Match with the Cerberus library, by
side-by-side implementation of examples.



Basic Usage
-----------


.. code-block:: python


    >>> document = {'name': 'john doe'}

    >>> schema = {'name': {'type': 'string'}}
    >>> v = Validator(schema)
    >>> v.validate(document)
    True

    >>> spec = {'name': str}
    >>> m = Match(spec)
    >>> m.matches(document)
    True



Nesting
-------


.. code-block:: python


    schema = {
        'person': {
            'type': 'dict',
            'schema': {
                'name': {'type': 'string', 'required': True, 'minlength': 2},
                'age': {'type': 'integer', 'required': True, 'min': 0},
            }
        }
    }

    spec = {
        'person': {
            'name': And(str, M(T.__len__() > 2))},
            'age': And(int, M(T > 0)),
        }
    }



Validating User Types
---------------------
Cerberus `apparently requires`_ a custom subclass of
``Validator`` with a ``_validate_type_<typename>``
method.


.. code-block:: python


    class UserClass: pass

    class UserValidator:
        def _validate_type_userclass(self, field, value):
            if not isinstance(value, UserClass):
                self._error(field, ERROR_BAD_TYPE.format('UserClass'))


.. _apparently requires: https://cerberus-sanhe.readthedocs.io/customize.html#new-types


None of this is needed in ``glom`` -- because python types match
instances of that type, ``UserClass`` can simply be used directly
in a spec.


.. code-block:: python


    UserClass  # value is an instance of user class
    [UserClass]  # value is a list of instances of user class
    {'data': UserClass}  # value['data'] is an instance of user class


Allow Extra Keys
----------------


Cerberus has a special keyword argument ``allow_unknown``
which is used to let the validator know that extra keys are
allowed.

``glom.Match`` because it can use types-as-keys, can simply
express "any key is allowed" with ``{object: object}``.

Moreover, ``glom.Match`` is much more flexible -- any condition
that can be applied to a value can also be applied to a key.

For example, maybe only string keys are allowed: ``{str: object}``.

Or, maybe anything but ``None`` is allowed as a key: ``{Not(None): object}``.



.. code-block:: python


    >>> v = Validator()
    >>> v.schema = {}
    >>> v.allow_unknown = True
    >>> v.validate({'name': 'john', 'sex': 'M'})
    True

    >>> Match({object: object})



Validating Nested Structures
----------------------------


.. code-block:: python


    >>> glom.Match({'outer': {str: int}}).validate({'outer': {'a': 1, 'b': 2}})


Extension
---------

Of note here is that glom is very careful about managing global modifications.



.. code-block:: python


    # cerberus custom validator
    from cerberus import Validator

    class MyValidator(Validator):
        def _validate_is_odd(self, constraint, field, value):
            """ Test the oddity of a value.

            The rule's arguments are validated against this schema:
            {'type': 'boolean'}
            """
            if constraint is True and not bool(value & 1):
                self._error(field, "Must be an odd number")

    # call the validator
    schema = {'amount': {'is odd': True, 'type': 'integer'}}


    # glom custom validator
    from glom import MatchError

    class IsOdd:
        def glomit(self, target, scope):
            if not value & 1:
                raise MatchError("{0} is not odd", target)

    # call the validator
    from glom import Match

    spec = Match({'amount': IsOdd()})

    # M and T in glom also allow these kind of expressions
    spec = M(T['amount'] & 1)



