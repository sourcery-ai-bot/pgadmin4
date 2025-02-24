##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

from abc import ABCMeta, abstractmethod

import six
from flask import url_for, render_template
from flask_babel import gettext
from pgadmin.browser import BrowserPluginModule
from pgadmin.browser.utils import PGChildModule
from pgadmin.utils import PgAdminModule
from pgadmin.utils.preferences import Preferences
from pgadmin.utils.constants import PGADMIN_NODE


@six.add_metaclass(ABCMeta)
class CollectionNodeModule(PgAdminModule, PGChildModule):
    """
    Base class for collection node submodules.
    """
    browser_url_prefix = BrowserPluginModule.browser_url_prefix
    SHOW_ON_BROWSER = True

    _BROWSER_CSS_PATH = 'browser/css'

    _NODE_CSS = "/".join([_BROWSER_CSS_PATH, 'node.css'])
    _COLLECTION_CSS = "/".join([_BROWSER_CSS_PATH, 'collection.css'])

    def __init__(self, import_name, **kwargs):
        kwargs.setdefault("url_prefix", self.node_path)
        kwargs.setdefault("static_url_path", '/static')

        PgAdminModule.__init__(self, f"NODE-{self.node_type}", import_name, **kwargs)
        PGChildModule.__init__(self)

    @property
    def jssnippets(self):
        """
        Returns a snippet of javascript to include in the page
        """
        return []

    @property
    def module_use_template_javascript(self):
        """
        Returns whether Jinja2 template is used for generating the javascript
        module.
        """
        return True

    def get_own_javascripts(self):
        scripts = []

        if self.module_use_template_javascript:
            scripts.extend(
                [
                    {
                        'name': PGADMIN_NODE % self.node_type,
                        'path': (
                            url_for('browser.index') + f'{self.node_type}/module'
                        ),
                        'when': self.script_load,
                        'is_template': True,
                    }
                ]
            )
        else:
            scripts.extend(
                [
                    {
                        'name': PGADMIN_NODE % self.node_type,
                        'path': url_for(
                            f'{self.name}.static', filename=f'js/{self.node_type}'
                        ),
                        'when': self.script_load,
                        'is_template': False,
                    }
                ]
            )

        for module in self.submodules:
            scripts.extend(module.get_own_javascripts())

        return scripts

    def generate_browser_node(
            self, node_id, parent_id, label, icon, **kwargs
    ):
        obj = {
            "id": f"{self.node_type}_{node_id}",
            "label": label,
            "icon": icon or self.node_icon,
            "inode": self.node_inode if 'inode' not in kwargs else kwargs['inode'],
            "_type": self.node_type,
            "_id": node_id,
            "_pid": parent_id,
            "module": PGADMIN_NODE % self.node_type,
        }
        for key in kwargs:
            obj.setdefault(key, kwargs[key])
        return obj

    def generate_browser_collection_node(self, parent_id, **kwargs):
        obj = {
            "id": "coll-%s_%d" % (self.node_type, parent_id),
            "label": self.collection_label,
            "icon": self.collection_icon,
            "inode": True,
            "_type": f'coll-{self.node_type}',
            "_id": parent_id,
            "_pid": parent_id,
            "module": PGADMIN_NODE % self.node_type,
            "nodes": [self.node_type],
        }

        for key in kwargs:
            obj.setdefault(key, kwargs[key])

        return obj

    @property
    def node_type(self):
        return f'{self._NODE_TYPE}'

    @property
    def csssnippets(self):
        """
        Returns a snippet of css to include in the page
        """
        snippets = [
            render_template(
                self._COLLECTION_CSS,
                node_type=self.node_type
            ),
            render_template(
                self._NODE_CSS,
                node_type=self.node_type,
                _=gettext
            )
        ]

        for submodule in self.submodules:
            snippets.extend(submodule.csssnippets)

        return snippets

    @property
    def collection_label(self):
        """
        Label to be shown for the collection node, do not forget to set the
        class level variable _COLLECTION_LABEL.
        """
        return gettext(self._COLLECTION_LABEL)

    @property
    def label(self):
        return gettext(self._COLLECTION_LABEL)

    @property
    def collection_icon(self):
        """
        icon to be displayed for the browser collection node
        """
        return f'icon-coll-{self.node_type}'

    @property
    def node_icon(self):
        """
        icon to be displayed for the browser nodes
        """
        return f'icon-{self.node_type}'

    @property
    def node_inode(self):
        """
        Override this property to make the node as leaf node.
        """
        return True

    @abstractmethod
    def get_nodes(self, sid, *args, **kwargs):
        """
        Generate the collection node
        You need to override this method because every node will have different
        url pattern for the parent.
        """
        pass

    @property
    def script_load(self):
        """
        This property defines, when to load this script.
        In order to allow creation of an object, we need to load script for any
        node at the parent level.

        i.e.
        - In order to allow creating a server object, it should be loaded at
          server-group node.
        """
        pass

    @property
    def node_path(self):
        return self.browser_url_prefix + self.node_type

    @property
    def javascripts(self):
        return []

    @property
    def show_node(self):
        """
        Property to check whether to show the node for this module on the
        browser tree or not.

        Relies on show_node preference object, otherwise on the SHOW_ON_BROWSER
        default value.
        """
        if self.pref_show_node:
            return self.pref_show_node.get()
        else:
            return self.SHOW_ON_BROWSER

    @property
    def show_system_objects(self):
        """
        Show/Hide the system objects in the database server.
        """
        if self.pref_show_system_objects:
            return self.pref_show_system_objects.get()
        else:
            return False

    def register_preferences(self):
        """
        register_preferences
        Register preferences for this module.

        Keep the browser preference object to be used by overriden submodule,
        along with that get two browser level preferences show_system_objects,
        and show_node will be registered to used by the submodules.
        """
        # Add the node informaton for browser, not in respective node
        # preferences
        self.browser_preference = Preferences.module('browser')
        self.pref_show_system_objects = self.browser_preference.preference(
            'show_system_objects'
        )
        self.pref_show_node = self.browser_preference.register(
            'node',
            f'show_node_{self.node_type}',
            self.collection_label,
            'node',
            self.SHOW_ON_BROWSER,
            category_label=gettext('Nodes'),
        )
