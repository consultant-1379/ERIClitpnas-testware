"""
@copyright: Ericsson Ltd
@since:     August 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-10456
"""
from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
import test_constants
import time


class Story10456(GenericTest):
    """
    LITPCDS-10456:
        As a LITP User I want NAS plugin to correctly handle rollback sync
        of restored/restoring NAS filesystems during remove_snapshot plans
    """

    def setUp(self):
        """Run before every test"""
        super(Story10456, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story10456, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story10456.xml"):
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

    def create_snapshot(self, expect_positive=True, plan_pass=True,
                        name=None, error_message=None):
        """
        Create the snapshot
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

    def remove_snapshots(self, cleanup=True, restore=False,
                         timeout_mins=2, default_time=10):
        """
        Deletes all snapshots
        """
        snapshot_url = self.find(self.ms_node, "/snapshots",
                                 "snapshot-base", assert_not_empty=False)
        list_of_snaps = []
        if restore:
            timeout_seconds = timeout_mins * 60
            seconds_passed = 0
            finished = False

            while not finished:
                self.execute_cli_removesnapshot_cmd(self.ms_node)
                if self.wait_for_plan_state(
                        self.ms_node, test_constants.PLAN_COMPLETE,
                        self.timeout_mins):
                    finished = True

                time.sleep(default_time)
                seconds_passed += default_time

                if seconds_passed > timeout_seconds:
                    return False

        else:
            for snap in snapshot_url:
                if snap == "/snapshots/snapshot":
                    self.execute_cli_removesnapshot_cmd(
                        self.ms_node, add_to_cleanup=cleanup)

                    # 1.b Verify that the remove snapshot plan succeeds.
                    self.assertTrue(self.wait_for_plan_state(
                        self.ms_node, test_constants.PLAN_COMPLETE,
                        self.timeout_mins))

                else:
                    snapshot_name = snap.split("/snapshots/").pop()
                    list_of_snaps.append(snapshot_name)

            if list_of_snaps:
                for snap in list_of_snaps:
                    args = "-n " + snap
                    self.execute_cli_removesnapshot_cmd(
                        self.ms_node, args=args, add_to_cleanup=cleanup)

                    # 1.b Verify that the remove snapshot plan succeeds.
                    self.assertTrue(self.wait_for_plan_state(
                        self.ms_node, test_constants.PLAN_COMPLETE,
                        self.timeout_mins))

    def write_to_node(self, file_path, node=None):
        """ Write a file to a mount point on a node and copy it several times.
        """
        node = node or self.nas_server
        size_kb = "1M"
        count = "100"
        cmd = "/bin/dd if=/dev/urandom of={0} bs={1} " \
              "count={2}".format(file_path, size_kb, count)
        self.run_command(node, cmd, username=self.sfs_server_user,

                         password=self.sfs_server_pw)
        for i in xrange(0, 100, 10):
            base = 'cp %s %s_%%s' % (file_path, file_path)
            cmd = '; '.join([base % (i * j) for j in xrange(10)])
            self.run_command(node, cmd, username=self.sfs_server_user,
                             password=self.sfs_server_pw,
                             connection_timeout_secs=2000)

    def grep_logs(self, message, node=None,
                  log=test_constants.GEN_SYSTEM_LOG_PATH):
        """
        Method to grep logs for given error message
        """
        node = node or self.ms_node
        stdout, stderr, rcode = self.run_command(
            node, self.rhc.get_grep_file_cmd(
                log, message),
            su_root=True)
        self.assertEqual(0, rcode)
        self.assertEqual([], stderr)
        self.assertNotEqual([], stdout)

    def offline_fs(self, fs_name):
        """
        Offline an sfs filesystem
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
        self.unmount_sfs_filesystem(self.nas_server, fs_name)

    def restore_fs(self, fs_name, snap_name):
        """ Restore a NAS filesystem
        """
        clish_path = '/opt/SYMCsnas/clish/bin/clish'  # VA clish path
        test = "/usr/bin/test -f %s"
        code = self.run_command(self.nas_server, test % clish_path,
                                username=self.sfs_server_user,
                                password=self.sfs_server_pw)[-1]
        if code != 0:
            # otherwise use SFS clish path
            clish_path = '/opt/VRTSnasgw/clish/bin/clish'
        cmd = "LANG=C SNAPSHOT_RESTORE_CONFIRM=YES %s -u master -c " \
              "'storage rollback restore %s %s'" % (clish_path, fs_name,
                                                    snap_name)

        self.run_command(self.nas_server, cmd,
                         username=self.sfs_server_user,
                         password=self.sfs_server_pw)

    @attr('all', 'revert', 'story10456', 'story10456_tc01')
    def test_01_n_remove_a_snapshot_while_it_is_restoring(self):
        """
        @tms_id: litpcds_10456_tc01
        @tms_requirements_id: LITPCDS-10456
        @tms_title: remove a snapshot while it is restoring
        @tms_description:Test that ensures we cannot remove an sfs snapshot if
            it is being used to restore an sfs-filesystem. We do the
            restore directly on the sfs as we don't need a full litp
            restore plan to run. It allows the test to be run quicker.
        @tms_test_steps:
        @step: Create sfs-cache item  under "/infrastructure"
        @result: item created
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: Create snapshot
        @result: snapshot plan executes successfully
        @step: make changes to the fs on the sfs
        @result: fs updated
        @step: offline the filesystem
        @result: filesystem is offline
        @step: issue storage rollback restore
        @result: restored is running
        @step: Remove snapshot
        @result: plan fails
        @result: message in var/log/messages: Deleting a snapshot is not
        permitted until the following file system(s) file_system1 are restored
        on the NAS
        @step: wait for restore to finish and run remove snapshot
        @result:  snapshot plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test01"
        file_system1 = "10456-fs1_a" + test_number
        file_systems = [file_system1]
        path1 = "/vx/" + file_system1
        file_path = path1 + "/testfile_1.txt"
        cache_name = "10456_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10456'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem1 = self.sfs_pools[0] + '/file_systems/fs1_10456_a' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props1 = "path=" + "'" + path1 + "' " + \
                                "size=" + "'" "20G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "50" "' "
        snapshot_name = "L_" + file_system1 + "_"

        # There are two alternative log messages to search for, as with VA 7.4
        # the message differed slightly. This message now accounts for SFS,
        # VA 7.2 and VA 7.4
        expected_error_logs = ['Deleting a snapshot is not permitted until '
                               'the following file system(s) \\"' +
                               file_system1
                               + r'\" are restored on the NAS\|Delete '
                                 'deployment snapshot \\"' + snapshot_name
                               + '\\" for file system with path \\"' + path1
                               + '\\" on NAS server']

        # 1. create an sfs-cache
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)
        # 2. create an sfs-filesystem fs1
        self.create_item(item_path=sfs_filesystem1,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props1,
                         xml_path=sfs_filesystem_xml)

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. make changes to the fs on the sfs
            self.write_to_node(file_path)
            # 5. run create_snapshot
            self.create_snapshot()
            # 6. make changes to the fs on the sfs
            self.write_to_node(file_path)
            # 7. check the sfs
            self.check_sfs(file_systems, cache_name=cache_name)
            # 8. offline the filesystem
            self.offline_fs(file_system1)
            # 9. issue a restore (rollback) directly on the sfs
            self.restore_fs(file_system1, snapshot_name)
            # 10. run remove_snapshot
            self.execute_cli_removesnapshot_cmd(self.ms_node)
            # 11. ensure the plan fails
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_FAILED, self.timeout_mins))
            # 12. check that the correct error is logged
            self.grep_logs(message=expected_error_logs)
            # 13. no snapshots should be deleted
            self.check_sfs(file_systems, snaps=file_systems)
            # 14. wait for the restore to finish
            self.remove_snapshots(restore=True, timeout_mins=5)
            # 15. plan should pass with success and snaps should be deleted
            self.check_sfs(file_systems, snaps=file_systems,
                           snap_present=False)

        finally:
            self.remove_snapshots()
            self.clean_sfs(file_systems)
