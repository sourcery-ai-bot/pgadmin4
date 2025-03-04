##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

import datetime
import json
import sys
import time


def debug(args, message):
    """ Print a debug message """
    if not args.debug:
        return

    now = datetime.datetime.now()

    print(f'[{now.strftime("%H:%M:%S")}]: {message}', file=sys.stderr, flush=True)


def error(args, message):
    """ Print an error message and exit """
    debug(args, message)

    output({'error': message})

    sys.exit(1)


def output(data):
    """ Dump JSON output from a dict """
    print(json.dumps(data), flush=True)
