##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################


import sys
import traceback

from regression.python_test_utils.test_utils import get_db_connection


def get_extension_data(schema_name):
    return {"name": "cube", "relocatable": "true", "schema": schema_name}


def create_extension(server, db_name, extension_name, schema_name):
    """
    This function used to create extension under the existing dummy database
    :param server: server details
    :type server: dict
    :param db_name: database name
    :type db_name: str
    :param extension_name: extension name to be added
    :type extension_name: str
    :param schema_name: schema name
    :type schema_name: str
    :return extension_id: extension id
    :rtype: int
    """
    try:
        connection = get_db_connection(db_name,
                                       server['username'],
                                       server['db_password'],
                                       server['host'],
                                       server['port'],
                                       server['sslmode'])
        old_isolation_level = connection.isolation_level
        connection.set_isolation_level(0)
        pg_cursor = connection.cursor()
        pg_cursor.execute(
            f'''CREATE EXTENSION "{extension_name}" SCHEMA "{schema_name}"'''
        )
        connection.set_isolation_level(old_isolation_level)
        connection.commit()
        # Get 'oid' from newly created extension
        pg_cursor.execute(
            f"SELECT oid FROM pg_catalog.pg_extension WHERE extname = '{extension_name}'"
        )
        extension_id = oid[0] if (oid := pg_cursor.fetchone()) else ''
        connection.close()
        return extension_id
    except Exception:
        traceback.print_exc(file=sys.stderr)


def verify_extension(server, db_name, extension_name):
    """
    This function will verify current extension.
    :param server: server details
    :type server: dict
    :param db_name: database name
    :type db_name: str
    :param extension_name: extension name to be added
    :type extension_name: str
    :return extension: extension detail
    :rtype: tuple
    """
    try:
        connection = get_db_connection(db_name,
                                       server['username'],
                                       server['db_password'],
                                       server['host'],
                                       server['port'],
                                       server['sslmode'])
        pg_cursor = connection.cursor()

        pg_cursor.execute("select * from pg_catalog.pg_extension "
                          "where extname='%s'" % extension_name)
        extension = pg_cursor.fetchone()
        connection.close()
        return extension
    except Exception:
        traceback.print_exc(file=sys.stderr)


def drop_extension(server, db_name, extension_name):
    """
    This function used to drop the extension.
    :param server: server details
    :type server: dict
    :param db_name: database name
    :type db_name: str
    :param extension_name: extension name
    :type extension_name: str
    :return: None
    """
    try:
        connection = get_db_connection(db_name,
                                       server['username'],
                                       server['db_password'],
                                       server['host'],
                                       server['port'],
                                       server['sslmode'])
        pg_cursor = connection.cursor()
        pg_cursor.execute(
            f"SELECT * FROM pg_catalog.pg_extension WHERE extname='{extension_name}'"
        )
        if pg_cursor.fetchall():
            pg_cursor.execute(f"DROP EXTENSION {extension_name} CASCADE")
            connection.commit()
        connection.close()
    except Exception:
        traceback.print_exc(file=sys.stderr)
