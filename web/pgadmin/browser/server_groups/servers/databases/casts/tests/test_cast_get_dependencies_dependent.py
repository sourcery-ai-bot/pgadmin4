##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2022, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################


from pgadmin.browser.server_groups.servers.databases.tests import \
    utils as database_utils
from pgadmin.utils.route import BaseTestGenerator
from regression import parent_node_dict
from regression.python_test_utils import test_utils as utils
from . import utils as cast_utils


class CastsGetDependentsAndDependencyTestCase(BaseTestGenerator):
    """ This class will fetch the cast node added under database node. """
    url = '/browser/cast/'
    scenarios = utils.generate_scenarios(
        "cast_get_dependencies_dependants", cast_utils.test_cases)

    def setUp(self):
        """ This function will create cast."""
        super(CastsGetDependentsAndDependencyTestCase, self).setUp()
        self.inv_data = self.inventory_data
        self.default_db = self.server["db"]
        self.database_info = parent_node_dict['database'][-1]
        self.db_name = self.database_info['db_name']
        self.server["db"] = self.db_name
        self.cast_id = cast_utils.create_cast(self.server,
                                              self.inv_data["srctyp"],
                                              self.inv_data["trgtyp"])

    def runTest(self):
        """ This function will fetch added cast."""
        self.server_id = self.database_info["server_id"]
        self.db_id = self.database_info['db_id']
        db_con = database_utils.connect_database(self,
                                                 utils.SERVER_GROUP,
                                                 self.server_id,
                                                 self.db_id)
        if db_con["info"] != "Database connected.":
            raise Exception("Could not connect to database.")

        if self.is_positive_test:
            if self.is_dependant:
                response = cast_utils.api_get_cast_node_dependent(self)
            else:
                response = cast_utils.api_get_cast_node_dependencies(self)

            cast_utils.assert_status_code(self, response)

    # TODO
    # Check weather to add -ve tests or not
    # as -ve scenarios NOT handled in code

    def tearDown(self):
        """This function disconnect the test database and drop added cast."""
        connection = utils.get_db_connection(self.server['db'],
                                             self.server['username'],
                                             self.server['db_password'],
                                             self.server['host'],
                                             self.server['port'],
                                             self.server['sslmode'])
        cast_utils.drop_cast(connection, self.inv_data["srctyp"],
                             self.inv_data["trgtyp"])
        database_utils.disconnect_database(self, self.server_id,
                                           self.db_id)
        self.server['db'] = self.default_db
