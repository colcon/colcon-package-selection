# Copyright 2020 Dirk Thomas
# Licensed under the Apache License, Version 2.0

import argparse
import re


def argument_valid_regex(value):
    """
    Check if an argument is a valid regular expression.

    Used as a ``type`` callback in ``add_argument()`` calls.

    :param str value: The command line argument
    :returns: The regular expression object
    :raises argparse.ArgumentTypeError: if the value is not a valid regex
    """
    try:
        return re.compile(value)
    except re.error as e:  # noqa: F841
        raise argparse.ArgumentTypeError(
            'must be a valid regex: {e}'.format_map(locals()))
