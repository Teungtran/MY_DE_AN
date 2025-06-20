from typing import Any, Callable, Optional, Sequence, Union

_NoDefault = object()  # Variable to indicate no default value is provided.


def get_value_from_dict(
    key: Union[str, Sequence[str]], data: dict, /, *, default: Optional[Any] = _NoDefault
) -> Callable:
    """Create a factory method that gets a value from a dictionary by a key path.

    Args:
        key: The key path to look up, either as a string or a list of keys.
            If a list of keys is provided, the first key found will be used.
        data: The dictionary in which the key(s) are searched.
    """

    def get_value_fn():
        """Retrieve a value from a dictionary based on a key path."""
        keys = key.split(".") if isinstance(key, str) else key
        res = data
        for k in keys:
            try:
                res = res[k]
            except KeyError:
                if default is _NoDefault:
                    msg = f"Did not find {keys} ({k} not found), please add an correct keys."
                    raise KeyError(msg)
                else:
                    return default
        return res

    return get_value_fn
