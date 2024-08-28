"""
@copyright: Ericsson Ltd
@since:     February 2016
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-10916
"""
from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
import test_constants
import time


class Story10916(GenericTest):
    """
    LITPCDS-10916:
        As a litp user I want to be able to use the nas plugin to
        configure multiple sfs pools under the same sfs service
    """

    def setUp(self):
        """Run before every test"""
        super(Story10916, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.xml = XMLUtils()
        self.sfs_services = self.find(self.ms_node, "/infrastructure",
                                      "sfs-service")
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3
        self.pool_name = "litp2_pool"

    def tearDown(self):
        """Run after every test"""
        super(Story10916, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story10916.xml"):
        """
        Description
            Exports the created item to xml file and Validates the xml file
            It then loads the xml and expects the correct error
        Actions:
            1: run export command on item path
            2: validate the xml file
            3. Loads the xml
            4. Expects an error
        """
        # EXPORT CREATED PROFILE ITEM
        self.execute_cli_export_cmd(self.ms_node, item_path, file_name)

        # validate xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, stderr, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], stdout)
        self.assertEqual(0, exit_code)
        self.assertEqual([], stderr)

        # this is done in each test to test the item with xml it an
        # already exists error is expected
        _, stderr, _ = self.execute_cli_load_cmd(
            self.ms_node, load_path, file_name, expect_positive=False)
        self.assertTrue(self.is_text_in_list("ItemExistsError", stderr))

    def create_item(self, item_path, item_type, item_props,
                    xml_path='', node=None, expect_positive=True,
                    error_type='', error_message=''):
        """
        Creates an item and expects the correct error if an error is supposed
        to exist
        """
        node = node or self.ms_node

        # Create the item
        _, stderr, _ = self.execute_cli_create_cmd(
            node, item_path, item_type,
            item_props, expect_positive=expect_positive)

        if expect_positive and item_type != "sfs-pool":
            # xml test
            self.xml_validator(item_path, xml_path)
        elif not expect_positive:
            # Check for error
            self.assertTrue(self.is_text_in_list(error_type, stderr),
                            error_message)

    def create_plan(self, node=None, expect_positive=True, error_type='',
                    error_message='',
                    plan_outcome=test_constants.PLAN_COMPLETE):
        """
        Method to create & run plan and expects errors
        """
        node = node or self.ms_node
        # run create_plan
        _, stderr, _ = self.execute_cli_createplan_cmd(
            node, expect_positive=expect_positive)

        if not expect_positive:
            # Check for error in create_plan
            self.assertTrue(self.is_text_in_list(error_type, stderr),
                            error_message)

        if expect_positive:
            # Perform the run_plan command
            self.execute_cli_runplan_cmd(node)
            self.assertTrue(self.wait_for_plan_state(node, plan_outcome))

    def clean_sfs(self, file_systems, snaps=(), paths=(), cache_name=None):
        """
        Method that cleans the sfs to it's previous state
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        if paths:
            for path in paths:
                self.delete_sfs_shares(self.nas_server, path)

        if snaps:
            for filesystem in file_systems:
                for snap in snaps:
                    snapshot = "L_" + filesystem + "_" + snap
                    self.assertTrue(self.delete_sfs_snapshot(
                        self.nas_server, snapshot, filesystem))

        for filesystem in file_systems:
            self.assertTrue(self.delete_sfs_fs(self.nas_server, filesystem))

        if cache_name is not None:
            self.assertTrue(self.delete_sfs_cache(self.nas_server,
                                                  cache_name))

    def check_sfs(self, file_system, snaps=(), snap_present=True,
                  cache_present=True, cache_name=None, cache_size=None,
                  fs_size=None, pool_name=None):
        """
        Method that checks the sfs for existing shares, filesystems,
        snapshots and caches
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        self.assertTrue(self.is_sfs_filesystem_present(
            self.nas_server, fs_name=file_system, size=fs_size,
            pool=pool_name))

        if snaps:
            if snap_present:
                for snap in snaps:
                    snapshot = "L_" + snap + "_"
                    self.assertTrue(self.is_sfs_snapshot_present(
                        self.nas_server, snapshot_name=snapshot))
            else:
                for snap in snaps:
                    self.assertFalse(self.is_sfs_snapshot_present(
                        self.nas_server, snapshot_name=snap))

        if cache_name is not None:
            if cache_present:
                self.assertTrue(self.is_sfs_cache_present(
                    self.nas_server, cache_name=cache_name,
                    cache_total=cache_size))

            else:
                self.assertFalse(self.is_sfs_cache_present(
                    self.nas_server, cache_name=cache_name,
                    cache_total=cache_size))

    def create_snapshot(self, expect_positive=True, plan_pass=True,
                        name=None, error_message=None):
        """
        Create the snapshot
        - expect_positive, if set to false, expects the create snapshot to
        throw an error before it is run.
        - plan_pass, if set to false, expects the create_snapshot
        plan to fail.
        """

        if name is not None:
            args = "-n " + name

        else:
            args = ''

        if expect_positive:
            # 1. Execute create_snapshot command
            self.execute_cli_createsnapshot_cmd(self.ms_node, args=args)

            if plan_pass:
                # 2. Verify that the create snapshot plan succeeds
                self.assertTrue(self.wait_for_plan_state(
                    self.ms_node, test_constants.PLAN_COMPLETE,
                    self.timeout_mins))

            else:
                # 2. Verify that the create snapshot plan fails
                self.assertFalse(self.wait_for_plan_state(
                    self.ms_node, test_constants.PLAN_COMPLETE,
                    self.timeout_mins))

        else:
            # 1. Execute create_snapshot command
            _, stderr, _ = self.execute_cli_createsnapshot_cmd(
                self.ms_node, args=args, expect_positive=False)
            self.assertTrue(stderr, error_message)

    def grep_logs(self, message, node=None,
                  log=test_constants.GEN_SYSTEM_LOG_PATH,
                  timeout_mins=2, default_time=10):
        """
        Method to grep logs for given error message
        """
        timeout_seconds = timeout_mins * 60
        seconds_passed = 0
        present = False
        while not present:
            node = node or self.ms_node
            stdout, stderr, rcode = self.run_command(
                node, self.rhc.get_grep_file_cmd(
                    log, message),
                su_root=True)
            self.assertEqual(0, rcode)
            self.assertEqual([], stderr)
            self.assertNotEqual([], stdout)
            present = True

            time.sleep(default_time)
            seconds_passed += default_time

            if seconds_passed > timeout_seconds:
                return False

    def update_item(self, item_path, item_props, node=None,
                    expect_positive=True, error_type='', error_message='',
                    action_del=False):
        """
        Updates an item and expects the correct error if an error is supposed
        to exist
        """
        node = node or self.ms_node

        # Update the item
        _, stderr, _ = self.execute_cli_update_cmd(
            node, item_path, props=item_props,
            expect_positive=expect_positive, action_del=action_del)

        if not expect_positive:
            # Check for error
            self.assertTrue(self.is_text_in_list(error_type, stderr),
                            error_message)

    @attr('all', 'revert', 'story10916', 'story10916_tc01')
    def test_01_p_multiple_pools_with_fs_and_cache_on_same_pool(self):
        """
        @tms_id: litpcds_10916_tc01
        @tms_requirements_id: LITPCDS-10916
        @tms_title: multiple pools with fs and cache on same pool
        @tms_description:Test that creates multiple sfs pools with a fs on each
        and a cache on one
        @tms_test_steps:
        @step: Create sfs-pool item  under "/infrastructure"
        @result: item created
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        sfs-cache
        @result: items created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        sfs-pool
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: Create snapshot
        @result: snapshot plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test01"
        file_system = "10916-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10916-fs2" + test_number
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10916_cache" + test_number
        sfs_pool = self.sfs_services[0] + '/pools/pool_10916' + test_number
        sfs_pool_props = "name=" + "'" + self.pool_name + "'"
        sfs_pool_xml = self.sfs_services[0] + '/pools'
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10916' \
                                      + test_number
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10916' \
                                           + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem2 = sfs_pool + '/file_systems/fs2_10916' + test_number
        sfs_filesystem_xml2 = sfs_pool + '/file_systems'
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10M" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "

        # 1. create an sfs-pool "litp2_pool"
        self.create_item(item_path=sfs_pool,
                         item_type="sfs-pool",
                         item_props=sfs_pool_props,
                         xml_path=sfs_pool_xml)
        # 2. create an sfs-cache
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)
        # 3. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 4. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml2)

        try:
            # 5. Create and run the plan
            self.create_plan()
            # 6. Ensure filesystems are created on the correct pools
            self.check_sfs(file_system, pool_name="litp2")
            self.check_sfs(file_system2, pool_name="litp2_pool")
            # 7. run create_snapshot
            self.create_snapshot()
            # 8. ensure the cache is the correct size and the
            # snapshots were created
            self.check_sfs(file_system, snaps=file_systems,
                           cache_name=cache_name, cache_size="6")

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)

    @attr('all', 'revert', 'story10916', 'story10916_tc02')
    def test_02_p_multiple_pools_with_fs_and_cache_on_different_pools(self):
        """
        @tms_id: litpcds_10916_tc02
        @tms_requirements_id: LITPCDS-10916
        @tms_title: multiple pools with fs and cache on same pool
        @tms_description:Test that creates multiple sfs pools with a fs on each
        and a cache on one
        @tms_test_steps:
        @step: Create sfs-pool item  under "/infrastructure"
        @result: item created
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        sfs-pool
        @result: items created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        sfs-pool
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: Create snapshot
        @result: snapshot plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test02"
        file_system = "10916-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10916-fs2" + test_number
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10916_cache" + test_number
        sfs_pool = self.sfs_services[0] + '/pools/pool_10916' + test_number
        sfs_pool_props = "name=" + "'" + self.pool_name + "'"
        sfs_pool_xml = self.sfs_services[0] + '/pools'
        sfs_cache = sfs_pool + '/cache_objects/cache_10916' + test_number
        sfs_cache_xml = sfs_pool + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10916' \
                                           + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs2_10916' \
                                            + test_number
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10M" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "

        # 1. create an sfs-pool "litp2_pool"
        self.create_item(item_path=sfs_pool,
                         item_type="sfs-pool",
                         item_props=sfs_pool_props,
                         xml_path=sfs_pool_xml)
        # 2. create an sfs-cache
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)
        # 3. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 4. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)

        try:
            # 5. Create and run the plan
            self.create_plan()
            # 6. Ensure filesystems are created on the correct pools
            self.check_sfs(file_system, pool_name="litp2")
            self.check_sfs(file_system2, pool_name="litp2")
            # 7. run create_snapshot
            self.create_snapshot()
            # 8. ensure the cache is the correct size and the
            # snapshots were created
            self.check_sfs(file_system, snaps=file_systems,
                           cache_name=cache_name, cache_size="6")

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)

    @attr('all', 'revert', 'story10916', 'story10916_tc03')
    def test_03_n_multiple_caches_across_multiple_pools(self):
        """
        @tms_id: litpcds_10916_tc03
        @tms_requirements_id: LITPCDS-10916
        @tms_title: multiple caches across multiple pools
        @tms_description:Test that creates 2 sfs pools and 2 caches, one
        on each pool
        @tms_test_steps:
        @step: Create sfs-cache item  under "/infrastructure" under pool1
        @result: item created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        under pool1
        @result: item created
        @step: Create sfs-filesystem item  under "/infrastructure" under
        under pool1
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @step: Create sfs-pool item  under "/infrastructure" under
        under litp2_pool
        @result: item created
        @step: Create sfs-pool item  under "/infrastructure" under
        under pool2
        @result: item created
        @step: Create snapshot
        @result: snapshot plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test03"
        file_system = "10916-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10916-fs2" + test_number
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10916_cache" + test_number
        sfs_pool = self.sfs_services[0] + '/pools/pool_10916' + test_number
        sfs_pool_props = "name=" + "'" + self.pool_name + "'"
        sfs_pool_xml = self.sfs_services[0] + '/pools'
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10916' \
                                      + test_number
        sfs_cache2 = sfs_pool + '/cache_objects/cache_10916' + test_number
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_xml2 = sfs_pool + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_cache_props2 = "name=" + "'" + cache_name + "_b" "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10916' \
                                           + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs2_10916' \
                                            + test_number
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10M" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        expected_error = 'Create plan failed: Only one sfs-cache is ' \
                         'allowed per sfs-service. ' \
                         'An sfs-cache with a ' \
                         '"name" property value of "' + cache_name + \
                         '" is already defined for the sfs-service ' \
                         'on path "' + sfs_cache + '".'

        # 1. create an sfs-cache on pool1
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 3. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)

        try:
            # 4. create and run plan
            self.create_plan()
            # 5. create an sfs-pool "litp2_pool"
            self.create_item(item_path=sfs_pool,
                             item_type="sfs-pool",
                             item_props=sfs_pool_props,
                             xml_path=sfs_pool_xml)
            # 6. create an sfs-cache on pool2
            self.create_item(item_path=sfs_cache2,
                             item_type="sfs-cache",
                             item_props=sfs_cache_props2,
                             xml_path=sfs_cache_xml2)
            # 7. Create plan and ensure the correct error is thrown
            self.create_plan(expect_positive=False,
                             error_type="ValidationError",
                             error_message=expected_error)
            # 8. run create_snapshot
            self.create_snapshot()
            # 9. ensure the cache is the correct size and the
            # snapshots were created
            self.check_sfs(file_system, snaps=file_systems,
                           cache_name=cache_name, cache_size="6")

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)

    @attr('all', 'revert', 'story10916', 'story10916_tc04')
    def test_04_n_empty_pool(self):
        """
        @tms_id: litpcds_10916_tc04
        @tms_requirements_id: LITPCDS-10916
        @tms_title: empty_pool
        @tms_description: Test that creates an sfs-pool with no child items
        @tms_test_steps:
        @step: Create sfs-pool item  under "/infrastructure" under litp2_pool
        @result: item created
        @step: Create sfs-cache item  under "/infrastructure" under
        under pool1
        @result: item created
        @step: Create two sfs-filesystem items under "/infrastructure" under
        under pool1
        @result: item created
        @step: Create plan
        @result: plan executes successfully
        @result: error thrown: ValidationError
        @result: message shown: Create plan failed: The sfs-pool with a
        property "name" value of "litp2_pool" must contain a minimum of
        one sfs-filesystem
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test04"
        file_system = "10916-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10916-fs2" + test_number
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10916_cache" + test_number
        sfs_pool = self.sfs_services[0] + '/pools/pool_10916' + test_number
        sfs_pool_props = "name=" + "'" + self.pool_name + "'"
        sfs_pool_xml = self.sfs_services[0] + '/pools'
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10916' \
                                      + test_number
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10916' \
                                           + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs2_10916' \
                                            + test_number
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10M" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        expected_error = 'Create plan failed: The sfs-pool with a property ' \
                         '"name" value of "' + self.pool_name + \
                         '" must contain a minimum of one sfs-cache or ' \
                         'sfs-filesystem.'

        # 1. create an sfs-pool "litp2_pool"
        self.create_item(item_path=sfs_pool,
                         item_type="sfs-pool",
                         item_props=sfs_pool_props,
                         xml_path=sfs_pool_xml)
        # 2. create an sfs-cache
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)
        # 3. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 4. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)

        try:
            # 5. Create and run the plan
            self.create_plan(expect_positive=False,
                             error_type="ValidationError",
                             error_message=expected_error)
            # 6. remove the pool and create and run plan
            self.execute_cli_remove_cmd(node=self.ms_node,
                                        url=sfs_pool)
            self.create_plan()
            # 7. recreate the pool
            self.create_item(item_path=sfs_pool,
                             item_type="sfs-pool",
                             item_props=sfs_pool_props,
                             xml_path=sfs_pool_xml)
            # 8. run create_snapshot
            self.create_snapshot()
            # 9. ensure the cache is the correct size and the
            # snapshots were created
            self.check_sfs(file_system, snaps=file_systems,
                           cache_name=cache_name, cache_size="6")

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)

    # This test is ignored on VA because there is an open issue regarding the
    # creation of file systems when a non-existent pool is specified. VA should
    # show an error but it doesn't. JIRA: TORF-IS-4149
    @attr('all', 'revert', 'story10916', 'story10916_tc05', 'sfs-only')
    def test_05_n_create_nonexistent_pool(self):
        """
        @tms_id: litpcds_10916_tc05
        @tms_requirements_id: LITPCDS-10916
        @tms_title: create nonexistent pool
        @tms_description: Test that creates an sfs-pool that doesn't exist
        on the sfs
        @tms_test_steps:
        @step: Create sfs-pool item  under "/infrastructure" with property
        name='nonexistent'
        @result: item created
        @step: Create two sfs-filesystem items under "/infrastructure" under
        under pool1
        @result: item created
        @step: Create and run plan
        @result: run plan fails
        @result: var/log/messages: Exception message: 'FS creation failed:
        SFS fs ERROR V-288-678 Pool(s) or disk(s) nonexistent does not exist
        @step: remove sfs-pool item
        @result: item removed
        @step: Create and run plan
        @result: plan executes successfully
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: update the two sfs-filesystem items with property
        cache_name and snap_size
        @result: items updated
        @step: create snapshot
        @result: snapshot plan fails
        @result: var/log/messages: Exception message: 'FS creation failed:
        SFS fs ERROR V-288-678 Pool(s) or disk(s) nonexistent does not exist
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test05"
        file_system = "10916-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10916-fs2" + test_number
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10916_cache" + test_number
        sfs_pool = self.sfs_services[0] + '/pools/pool_10916' + test_number
        sfs_pool_props = "name=" + "'" + "nonexistent" + "'"
        sfs_pool_xml = self.sfs_services[0] + '/pools'
        sfs_cache = sfs_pool + '/cache_objects/cache_10916' + test_number
        sfs_cache_xml = sfs_pool + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10916' \
                                           + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_filesystem2 = sfs_pool + '/file_systems/fs2_10916' + test_number
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10M" "'"
        sfs_filesystem_xml2 = sfs_pool + '/file_systems'
        sfs_filesystem_props3 = "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        expected_log_message = "Exception message: 'FS creation failed: " \
                               "SFS fs ERROR V-288-678 Pool(s) or disk(s) " \
                               "nonexistent does not exist"

        # 1. create an sfs-pool "nonexistent"
        self.create_item(item_path=sfs_pool,
                         item_type="sfs-pool",
                         item_props=sfs_pool_props,
                         xml_path=sfs_pool_xml)
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 3. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml2)

        try:
            # 4. Create and run the plan
            self.create_plan(plan_outcome=test_constants.PLAN_FAILED)
            # 5. check the logs for the correct message
            self.grep_logs(message=expected_log_message)
            # 6. remove the pool and create and run plan
            self.execute_cli_remove_cmd(node=self.ms_node,
                                        url=sfs_pool)
            self.create_plan()
            # 7. recreate the pool
            self.create_item(item_path=sfs_pool,
                             item_type="sfs-pool",
                             item_props=sfs_pool_props,
                             xml_path=sfs_pool_xml)
            # 8. create an sfs-cache
            self.create_item(item_path=sfs_cache,
                             item_type="sfs-cache",
                             item_props=sfs_cache_props,
                             xml_path=sfs_cache_xml)
            # 9. update the filesystems to add cache_name and snap_size
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            # 10. run create_snapshot
            self.create_snapshot(plan_pass=False)
            # 11 check the logs for the correct message
            self.grep_logs(message=expected_log_message)

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)
