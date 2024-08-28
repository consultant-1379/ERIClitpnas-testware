"""
@copyright: Ericsson Ltd
@since:     October 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-10947
"""
import os
import time
import test_constants
from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils


class Story10947(GenericTest):
    """
    LITPCDS-10947:
        Nas plugin shall define separate tasks for checking sfs
        cache and the snapshots in the restore snapshot plan.
    """

    def setUp(self):
        """Run before every test"""
        super(Story10947, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story10947, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story10947.xml"):
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

    def check_sfs(self, file_systems, snaps=(), snap_present=True,
                  cache_present=True, cache_name=None, cache_size=None,
                  fs_size=None):
        """
        Method that checks the sfs for existing shares, filesystems,
        snapshots and caches
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        if file_systems:
            for filesystem in file_systems:
                self.assertTrue(self.is_sfs_filesystem_present(
                    self.nas_server, fs_name=filesystem, size=fs_size))

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

    def cache_full(self, cache_name, timeout_mins=1, default_time=10):
        """
        Checks the cache is full
        """
        timeout_seconds = timeout_mins * 60
        seconds_passed = 0

        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
        while True:
            if self.is_sfs_cache_present(
                    self.nas_server, cache_name=cache_name,
                    cache_available="0", cache_percent_available="0"):
                return True

            time.sleep(default_time)
            seconds_passed += default_time

            if seconds_passed > timeout_seconds:
                return False

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

    def restore_snapshot(self, expect_positive=True, error_message=None,
                         plan_pass=True):
        """
        Restore the snapshot
        - expect_positive, is set to false, expects the restore_snapshot
        to throw an error before the plan is run.
        - plan_pass, if set to False, expects the restore_snapshot plan
        to fail.
        """
        if expect_positive:
            # Execute restore_snapshot command
            self.execute_cli_restoresnapshot_cmd(self.ms_node)

            if plan_pass:
                # Verify that the restore snapshot plan succeeds
                self.assertTrue(self.wait_for_plan_state(
                    self.ms_node, test_constants.PLAN_COMPLETE,
                    self.timeout_mins))

            else:
                # Verify that the restore snapshot plan fails
                self.assertFalse(self.wait_for_plan_state(
                    self.ms_node, test_constants.PLAN_COMPLETE,
                    self.timeout_mins))

        else:
            # Execute restore_snapshot command
            _, stderr, _ = self.execute_cli_restoresnapshot_cmd(
                self.ms_node, expect_positive=False)
            self.assertTrue(stderr, error_message)

    def write_to_sfs(self, path, size='1M'):
        """ Write a file to a SFS file system
        """
        cmd = "/bin/dd if=/dev/urandom of=%s bs=%s count=1" % (path, size)
        self.run_command(self.nas_server, cmd, username=self.sfs_server_user,
                         password=self.sfs_server_pw)

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

    @attr('all', 'revert', 'story10947', 'story10947_tc01')
    def test_01_n_manually_remove_a_snapshot_before_restore(self):
        """
        @tms_id: litpcds_10947_tc01
        @tms_requirements_id: LITPCDS-10947
        @tms_title: manually remove a snapshot before restore
        @tms_description: Test that manually removes an sfs snapshot before we
        run a restore
        @tms_test_steps:
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: Create two sfs-filesystem items under "/infrastructure"
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @step: create snapshot
        @result: snapshot plan succeeds
        @step: remove snapshot on the sfs manually
        @result: snapshot removed
        @step: remove_snapshot
        @result: snapshot plan fails
        @result: var/log/messages: The snapshot %s doesn't exist on NAS
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        file_systems = []
        test_number = "_test01"
        file_system = "10947-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10947-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "10947_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10947'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10947' \
                                           + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_10947' \
                                            + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "20G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        snapshot_name = "L_" + file_system + "_"
        expected_error_logs = ["The snapshot %s doesn't exist on NAS" %
                               snapshot_name]

        # 1. create an sfs-cache
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
            # 4. Create and run the plan
            self.create_plan()
            # 5. Ensure filesystems are created
            self.check_sfs(file_systems)
            # 6. run create_snapshot
            self.create_snapshot()
            # 7. Check the sfs
            self.check_sfs(file_systems, snaps=file_systems,
                           cache_name=cache_name, cache_size="3072")
            # 8. remove a snapshot directly on the sfs for one of
            # the filesystems
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            self.assertTrue(self.delete_sfs_snapshot(
                self.nas_server, snapshot_test=snapshot_name,
                fs_test=file_system))
            # 9. run restore_snapshot and ensure it fails
            self.restore_snapshot(plan_pass=False)
            # 10. grep the logs for the correct message
            self.grep_logs(message=expected_error_logs)

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)

    @attr('all', 'revert', 'story10947', 'story10947_tc02')
    def test_02_n_ensure_restore_fails_when_cache_is_full(self):
        """
        @tms_id: litpcds_10947_tc02
        @tms_requirements_id: LITPCDS-10947
        @tms_title: ensure restore fails when cache is full
        @tms_description: Test that fills up an sfs cache before running
        restore_snapshot
        @tms_test_steps:
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: Create two sfs-filesystem items under "/infrastructure"
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @step: create snapshot
        @result: snapshot plan succeeds
        @step:  copy files to the sfs to fill up the cache
        @result: files copied to sfs
        @step: execute litp restore_snapshot
        @result: snapshot plan fails
        @result: var/log/messages: Snapshot(s) corrupted because no space is
        available on NAS cache
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_all_snapshots(node=self.ms_node)
        test_number = "_test02"
        file_system = "10947-fs1" + test_number
        file_system2 = "10947-fs1_b" + test_number
        file_systems = [file_system, file_system2]
        path = "/vx/" + file_system
        path2 = "/vx/" + file_system2
        cache_name = "10947_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10947'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10947' \
                                           + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_10947_b' \
                                            + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "20M" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        expected_error_logs = ['\'Snapshot(s) corrupted because no space is '
                               'available on NAS cache '
                               '\\"' + cache_name + '\\".\'']

        # 1. create an sfs-cache
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
            # 3. Create and run the plan
            self.create_plan()
            # 4. Ensure filesystems are created
            self.check_sfs(file_systems)
            # 5. run create_snapshot
            self.create_snapshot()
            # 6. Check the sfs
            self.check_sfs(file_systems)
            # 7. copy files to the sfs to fill up the cache
            for i in xrange(5):
                self.write_to_sfs(os.path.join(path, "testfile%s.dat" % i))
                self.write_to_sfs(os.path.join(path2, "testfile%s.dat" % i))
            # 8. Wait for cache to fill
            self.assertTrue(self.cache_full(cache_name))
            # 9. run restore_snapshot and ensure it fails
            self.restore_snapshot(plan_pass=False)
            # 10. grep the logs for the correct message
            self.grep_logs(message=expected_error_logs)

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems)
