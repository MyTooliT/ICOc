# Style

Please use the guidelines from [PEP 8](https://www.python.org/dev/peps/pep-0008/). For code formatting we currently use [YAPF](https://github.com/google/yapf), which should format code according to PEP 8 by default.

To format the whole code base you can use the following command in the root of the repository:

```sh
yapf --in-place --parallel --recursive .
```

YAPF will not

- split long strings and
- add newlines to long lines not surrounded by parentheses.

To make sure that code has a maximum line length of `79` characters please split up long strings and add parentheses yourself.

For development we recommend that you use a tool or plugin that reformats your code with YAPF every time you save. This way we can ensure that we use a consistent style for the whole code base.
