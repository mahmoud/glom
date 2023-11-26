# glom

*Restructuring data, the Python way*

<a href="https://pypi.org/project/glom/"><img src="https://img.shields.io/pypi/v/glom.svg"></a>
<a href="https://calver.org/"><img src="https://img.shields.io/badge/calver-YY.MM.MICRO-22bfda.svg"></a>

<img width="30%" align="right" src="https://raw.githubusercontent.com/mahmoud/glom/master/docs/_static/comet.png">

Real applications have real data, and real data nests. Objects inside
of objects inside of lists of objects.

glom is a new and powerful way to handle real-world data, featuring:

* Path-based access for nested data structures
* Readable, meaningful error messages
* Declarative data transformation, using lightweight, Pythonic specifications
* Built-in data exploration and debugging features

All of that and more, available as a [fully-documented][rtd],
pure-Python package, tested on Python 3.7+, as well as
PyPy3. Installation is as easy as:

```
  pip install glom
```

And when you install glom, you also get [the `glom` command-line
interface][cli_rtd], letting you experiment at the console, but never limiting
you to shell scripts:

```
Usage: glom [FLAGS] [spec [target]]

Command-line interface to the glom library, providing nested data access and data
restructuring with the power of Python.

Flags:

  --help / -h                     show this help message and exit
  --target-file TARGET_FILE       path to target data source (optional)
  --target-format TARGET_FORMAT
                                  format of the source data (json, python, toml,
                                  or yaml) (defaults to 'json')
  --spec-file SPEC_FILE           path to glom spec definition (optional)
  --spec-format SPEC_FORMAT       format of the glom spec definition (json, python,
                                    python-full) (defaults to 'python')
  --indent INDENT                 number of spaces to indent the result, 0 to disable
                                    pretty-printing (defaults to 2)
  --debug                         interactively debug any errors that come up
  --inspect                       interactively explore the data

```

Anything you can do at the command line readily translates to Python
code, so you've always got a path forward when complexity starts to
ramp up.


## Examples
#### Without glom
```python
>>> data = {'a': {'b': {'c': 'd'}}}
>>> data['a']['b']['c']
'd'
>>> data2 = {'a': {'b': None}}
>>> data2['a']['b']['c']
Traceback (most recent call last):
...
TypeError: 'NoneType' object is not subscriptable
```

#### With glom
```python
>>> glom(data, 'a.b.c')
'd'
>>> glom(data2, 'a.b.c')
Traceback (most recent call last):
...
PathAccessError: could not access 'c', index 2 in path Path('a', 'b', 'c'), got error: ...
```

## Learn more

<img width="30%" align="right" src="https://raw.githubusercontent.com/mahmoud/glom/master/docs/_static/comet_multi.png">

If all this seems interesting, continue exploring glom below:

* [glom Tutorial][tutorial]
* [Full API documentation at Read the Docs][rtd]
* [Original announcement blog post (2018-05-09)][glom_announce]
* [Frequently Asked Questions][faq]
* [PyCon 2018 Lightning Talk (2018-05-11)][pycon_talk]

All of the links above are overflowing with examples, but should you
find anything about the docs, or glom itself, lacking, [please submit
an issue][gh_issues]!

[rtd]: https://glom.readthedocs.io
[cli_rtd]: http://glom.readthedocs.io/en/latest/cli.html
[tutorial]: https://glom.readthedocs.io/en/latest/tutorial.html
[faq]: https://glom.readthedocs.io/en/latest/faq.html
[glom_announce]: https://sedimental.org/glom_restructured_data.html
[gh_issues]: https://github.com/mahmoud/glom/issues/
[pycon_talk]: https://www.youtube.com/watch?v=bTAFl8P2DkE&t=18m07s

In the meantime, just remember: When you've got nested data, glom it! ☄️
