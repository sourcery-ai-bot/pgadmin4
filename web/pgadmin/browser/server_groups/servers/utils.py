##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Server helper utilities"""
from ipaddress import ip_address

from pgadmin.utils.crypto import encrypt, decrypt
import config
from pgadmin.model import db, Server


def is_valid_ipaddress(address):
    try:
        return bool(ip_address(address))
    except ValueError:
        return False


def parse_priv_from_db(db_privileges):
    """
    Common utility function to parse privileges retrieved from database.
    """
    acl = {
        'grantor': db_privileges['grantor'],
        'grantee': db_privileges['grantee'],
        'privileges': []
    }
    if 'acltype' in db_privileges:
        acl['acltype'] = db_privileges['acltype']

    privileges = [
        {
            "privilege_type": priv,
            "privilege": True,
            "with_grant": db_privileges['grantable'][idx],
        }
        for idx, priv in enumerate(db_privileges['privileges'])
    ]
    acl['privileges'] = privileges

    return acl


def _check_privilege_type(priv):
    if (
        not isinstance(priv['privileges'], dict)
        or 'changed' not in priv['privileges']
    ):
        return
    tmp = []
    for p in priv['privileges']['changed']:
        tmp_p = {'privilege_type': p['privilege_type'],
                 'privilege': False,
                 'with_grant': False}

        if 'with_grant' in p:
            tmp_p['privilege'] = True
            tmp_p['with_grant'] = p['with_grant']

        if 'privilege' in p:
            tmp_p['privilege'] = p['privilege']

        tmp.append(tmp_p)

    priv['privileges'] = tmp


def _parse_privileges(priv, db_privileges, allowed_acls, priv_with_grant,
                      priv_without_grant):
    _check_privilege_type(priv)
    for privilege in priv['privileges']:

        if privilege['privilege_type'] not in db_privileges:
            continue

        if privilege['privilege_type'] not in allowed_acls:
            continue

        if privilege['with_grant']:
            priv_with_grant.append(
                db_privileges[privilege['privilege_type']]
            )
        elif privilege['privilege']:
            priv_without_grant.append(
                db_privileges[privilege['privilege_type']]
            )


def parse_priv_to_db(str_privileges, allowed_acls=[]):
    """
    Common utility function to parse privileges before sending to database.
    """
    from pgadmin.utils.driver import get_driver
    from config import PG_DEFAULT_DRIVER
    driver = get_driver(PG_DEFAULT_DRIVER)

    db_privileges = {
        'c': 'CONNECT',
        'C': 'CREATE',
        'T': 'TEMPORARY',
        'a': 'INSERT',
        'r': 'SELECT',
        'w': 'UPDATE',
        'd': 'DELETE',
        'D': 'TRUNCATE',
        'x': 'REFERENCES',
        't': 'TRIGGER',
        'U': 'USAGE',
        'X': 'EXECUTE'
    }

    privileges = []
    allowed_acls_len = len(allowed_acls)

    for priv in str_privileges:
        priv_with_grant = []
        priv_without_grant = []

        _parse_privileges(priv, db_privileges, allowed_acls, priv_with_grant,
                          priv_without_grant)

        # If we have all acl then just return all
        if len(priv_with_grant) == allowed_acls_len > 1:
            priv_with_grant = ['ALL']
        if len(priv_without_grant) == allowed_acls_len > 1:
            priv_without_grant = ['ALL']

        grantee = driver.qtIdent(None, priv['grantee']) \
            if priv['grantee'] != 'PUBLIC' else 'PUBLIC'

        old_grantee = driver.qtIdent(None, priv['old_grantee']) \
            if 'old_grantee' in priv and priv['old_grantee'] != 'PUBLIC' \
            else grantee

        acltype = priv['acltype'] if 'acltype' in priv else 'defaultacls'

        # Appending and returning all ACL
        privileges.append({
            'grantor': priv['grantor'],
            'grantee': grantee,
            'with_grant': priv_with_grant,
            'without_grant': priv_without_grant,
            'old_grantee': old_grantee,
            'acltype': acltype
        })

    return privileges


def tokenize_options(options_from_db, option_name, option_value):
    """
    This function will tokenize the string stored in database
    e.g. database store the value as below
    key1=value1, key2=value2, key3=value3, ....
    This function will extract key and value from above string

    Args:
        options_from_db: Options from database
        option_name: Option Name
        option_value: Option Value

    Returns:
        Tokenized options
    """
    options = []
    if options_from_db is not None:
        for fdw_option in options_from_db:
            k, v = fdw_option.split('=', 1)
            options.append({option_name: k, option_value: v})
    return options


def validate_options(options, option_name, option_value):
    """
    This function will filter validated options
    and sets flag to use in sql template if there are any
    valid options

    Args:
        options: List of options
        option_name: Option Name
        option_value: Option Value

    Returns:
        Flag, Filtered options
    """
    valid_options = []
    for option in options:
        # If option name is valid
        if option_name in option and \
            option[option_name] is not None and \
                option[option_name] != '' and \
                len(option[option_name].strip()) > 0:
            # If option value is valid
            if (
                option_value not in option
                or option[option_value] is None
                or option[option_value] == ''
                or len(option[option_value].strip()) <= 0
            ):
                # Set empty string if no value provided
                option[option_value] = ''
            valid_options.append(option)

    is_valid_options = bool(valid_options)
    return is_valid_options, valid_options


def _password_check(server, manager, old_key, new_key):
    # Check if old password was stored in pgadmin4 sqlite database.
    # If yes then update that password.
    if server.password is not None:
        password = decrypt(server.password, old_key)

        if isinstance(password, bytes):
            password = password.decode()

        password = encrypt(password, new_key)
        setattr(server, 'password', password)
        manager.password = password


def reencrpyt_server_passwords(user_id, old_key, new_key):
    """
    This function will decrypt the saved passwords in SQLite with old key
    and then encrypt with new key
    """
    from pgadmin.utils.driver import get_driver
    driver = get_driver(config.PG_DEFAULT_DRIVER)

    for server in Server.query.filter_by(user_id=user_id).all():
        manager = driver.connection_manager(server.id)

        _password_check(server, manager, old_key, new_key)

        if server.tunnel_password is not None:
            tunnel_password = decrypt(server.tunnel_password, old_key)
            if isinstance(tunnel_password, bytes):
                tunnel_password = tunnel_password.decode()

            tunnel_password = encrypt(tunnel_password, new_key)
            setattr(server, 'tunnel_password', tunnel_password)
            manager.tunnel_password = tunnel_password
        elif manager.tunnel_password is not None:
            tunnel_password = decrypt(manager.tunnel_password, old_key)

            if isinstance(tunnel_password, bytes):
                tunnel_password = tunnel_password.decode()

            tunnel_password = encrypt(tunnel_password, new_key)
            manager.tunnel_password = tunnel_password

        db.session.commit()
        manager.update_session()


def remove_saved_passwords(user_id):
    """
    This function will remove all the saved passwords for the server
    """

    try:
        db.session.query(Server) \
            .filter(Server.user_id == user_id) \
            .update({Server.password: None, Server.tunnel_password: None})
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def does_server_exists(sid, user_id):

    """
    This function will return True if server is existing for a user
    :param sid: server id
    :param user_id: user id
    :return: Boolean
    """
    # **kwargs parameter can be added to function to filter with more
    # parameters.
    try:
        return Server.query.filter_by(id=sid).first() is not None
    except Exception:
        return False
