"""Type checking code"""


def check_list(
    data: object, required_length: int, argument_name="data"
) -> None:
    """Check if the given object is a list with the given length

    Parameters
    ----------

    data:
        The object that should be checked for list type

    required_length:
        The required minimum length of the object, if it is a list

    argument_name:
        The variable name of the given object

    Raises
    ------

    A ValueError if the given object is not a list or is too long

    """

    if not isinstance(data, list):
        raise ValueError(
            f"Unsupported object type for argument {argument_name}: "
            f"“{type(data)}”"
        )
    if len(data) < required_length:
        raise ValueError(
            f"Data length of {len(data)} is too "
            "small, at least length of "
            f"“{required_length}” required"
        )
