##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""A blueprint module implementing the about box."""

from flask import Response, render_template, url_for, request
from flask_babel import gettext
from flask_security import current_user, login_required
from pgadmin.utils import PgAdminModule
from pgadmin.utils.menu import MenuItem
from pgadmin.utils.constants import MIMETYPE_APP_JS
import config
import httpagentparser
from pgadmin.model import User
from user_agents import parse
import platform

MODULE_NAME = 'about'


class AboutModule(PgAdminModule):
    def get_own_menuitems(self):
        appname = config.APP_NAME

        return {
            'help_items': [
                MenuItem(
                    name='mnu_about',
                    priority=999,
                    module="pgAdmin.About",
                    callback='about_show',
                    icon='fa fa-info-circle',
                    label=gettext('About %(appname)s', appname=appname)
                )
            ]
        }

    def get_own_javascripts(self):
        return [{
            'name': 'pgadmin.about',
            'path': url_for('about.index') + 'about',
            'when': None
        }]

    def get_exposed_url_endpoints(self):
        return ['about.index']


blueprint = AboutModule(MODULE_NAME, __name__, static_url_path='')


##########################################################################
# A test page
##########################################################################
@blueprint.route("/", endpoint='index')
@login_required
def index():
    """Render the about box."""
    info = {}
    # Get OS , NW.js, Browser details
    browser, os_details, nwjs_version = detect_browser(request)

    if nwjs_version:
        info['nwjs'] = nwjs_version

    info['browser_details'] = browser
    info['os_details'] = os_details
    info['config_db'] = config.SQLITE_PATH
    info['log_file'] = config.LOG_FILE

    if config.SERVER_MODE:
        info['app_mode'] = gettext('Server')
        admin = is_admin(current_user.email)
        info['admin'] = admin
    else:
        info['app_mode'] = gettext('Desktop')

    info['current_user'] = current_user.email

    settings = ""
    for setting in dir(config):
        if not setting.startswith('_') and setting.isupper() and \
            setting not in ['CSRF_SESSION_KEY',
                            'SECRET_KEY',
                            'SECURITY_PASSWORD_SALT',
                            'SECURITY_PASSWORD_HASH',
                            'ALLOWED_HOSTS',
                            'MAIL_PASSWORD',
                            'LDAP_BIND_PASSWORD',
                            'SECURITY_PASSWORD_HASH']:
            if isinstance(getattr(config, setting), str):
                settings = f'{settings}{setting} = "{getattr(config, setting)}"\n'
            else:
                settings = f'{settings}{setting} = {getattr(config, setting)}\n'

    info['settings'] = settings

    return render_template(f'{MODULE_NAME}/index.html', info=info, _=gettext)


def is_admin(load_user):
    user = User.query.filter_by(email=load_user).first()
    return user.has_role("Administrator")


def detect_browser(request):
    """This function returns the browser and os details"""
    nwjs_version = None
    agent = request.environ.get('HTTP_USER_AGENT')
    os_details = parse(platform.platform()).ua_string

    if 'Nwjs' in agent:
        agent = agent.split('-')
        nwjs_version = agent[0].split(':')[1]
        browser = 'Chromium' + ' ' + agent[2]

    else:
        browser = httpagentparser.detect(agent)
        browser = (
            browser['browser']['name'] + ' ' + browser['browser']['version']
            if browser
            else agent.split('/')[0]
        )
    return browser, os_details, nwjs_version


@blueprint.route("/about.js")
@login_required
def script():
    """render the required javascript"""
    return Response(
        response=render_template("about/about.js", _=gettext),
        status=200,
        mimetype=MIMETYPE_APP_JS
    )
