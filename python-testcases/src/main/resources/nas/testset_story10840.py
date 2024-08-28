"""
@copyright: Ericsson Ltd
@since:     September 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-10840
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from xml_utils import XMLUtils
import test_constants
import time
import socket
import exceptions
import sys


class Story10840(GenericTest):
    """
    LITPCDS-10840:
        As a LITP User I want NAS plugin to correctly handle rollback sync
        of already restoring SFS filesystems during restore_snapshot plans
    """

    def setUp(self):
        """Run before every test"""
        super(Story10840, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.xml = XMLUtils()
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3
        self.rhcmd = RHCmdUtils()

    def tearDown(self):
        """Run after every test"""
        super(Story10840, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story10840.xml"):
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
                    error_type='', error_message='', add_to_cleanup=True):
        """
        Creates an item and expects the correct error if an error is supposed
        to exist
        """
        node = node or self.ms_node

        # Create the item
        _, stderr, _ = self.execute_cli_create_cmd(
            node, item_path, item_type,
            item_props, add_to_cleanup=add_to_cleanup,
            expect_positive=expect_positive)

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

    def clean_sfs(self, file_systems, snaps=(), path=None, cache_name=None):
        """
        Method that cleans the sfs to it's previous state
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        if path:
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

    def check_sfs(self, file_systems=None, path=None):
        """
        Method that checks the sfs for existing shares, filesystems,
        snapshots and caches
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
        if path:
            self.assertTrue(self.is_sfs_share_present(self.nas_server, path))

        if file_systems:
            for filesystem in file_systems:
                self.assertTrue(self.is_sfs_filesystem_present(
                    self.nas_server, fs_name=filesystem))

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
        """
        Write a file to a mount point on a node
        """
        node = node or self.nas_server

        size_kb = "1M"
        count = "8000"
        cmd = "/bin/dd if=/dev/urandom of={0} bs={1} " \
              "count={2}".format(file_path, size_kb, count)

        self.run_command(node, cmd, username=self.sfs_server_user,
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

    def _verify_restore_snapshot_completes(self):
        """
            verify restore snapshot completes
        """
        self.assertTrue(self._node_rebooted(self.ms_node))
        self.assertTrue(self._litp_up())
        self.assertTrue(self._m_nodes_up())

    def _up_time(self, node):
        """
            Return uptime of node
        """
        cmd = self.rhcmd.get_cat_cmd('/proc/uptime')
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertEqual(0, ret_code)
        self.assertEqual([], err)
        self.assertNotEqual([], out)
        uptime_seconds = float(out[0].split()[0])
        return uptime_seconds

    def _node_rebooted(self, node):
        """
            Verify that a node  has rebooted.
        """
        node_restarted = False
        max_duration = 1800
        elapsed_sec = 0
        # uptime before reboot
        up_time_br = self._up_time(node)
        while elapsed_sec < max_duration:
            # if True:
            try:
                # uptime after reboot
                up_time_ar = self._up_time(node)
                self.log("info", "{0} is up for {1} seconds"
                         .format(node, str(up_time_ar)))

                if up_time_ar < up_time_br:
                    self.log("info", "{0} has been rebooted"
                             .format(node))
                    node_restarted = True
                    break
            except (socket.error, exceptions.AssertionError):
                self.log("info", "{0} is not up at the moment"
                         .format(node))
            except:
                self.log("error", "Reboot check. Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))
                self.disconnect_all_nodes()

            time.sleep(10)
            elapsed_sec += 10

        if not node_restarted:
            self.log("error", "{0} not rebooted in last {1} seconds."
                     .format(node, str(max_duration)))
        return node_restarted

    def _litp_up(self):
        """
            Verify that the MS has a working litp instance
        """
        litp_up = False
        max_duration = 300
        elapsed_sec = 0

        while elapsed_sec < max_duration:
            try:
                _, _, exit_code = self.get_service_status(self.ms_node,
                                                          'litpd')
                if exit_code == 0:
                    self.log("info", "Litp is up")
                    litp_up = True
                    break

                else:
                    self.log("info", "Litp is not up")

            except (socket.error, exceptions.AssertionError):
                self.log("info", "Litp is not up after {0} seconds"
                         .format(elapsed_sec))
            except:
                self.log("error", "Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))

            time.sleep(10)
            elapsed_sec += 10

        if not litp_up:
            self.log("error", "Litp is not up in last {0} seconds."
                     .format(str(max_duration)))
        return litp_up

    def _m_nodes_up(self):
        """
            Verify that the MS has a working litp instance
        """
        m_nodes_up = False
        max_duration = 300
        elapsed_sec = 0
        cmd = "/bin/hostname"
        while elapsed_sec < max_duration:
            try:
                _, _, ret_code = self.run_command(self.mn_nodes[0], cmd)
                self.assertEqual(0, ret_code)
                if ret_code == 0:
                    m_nodes_up = True
                    break
                else:
                    self.log("info", "Node {0} is not up in last {1} seconds."
                             .format(self.mn_nodes[0], elapsed_sec))
            except (socket.error, exceptions.AssertionError):
                self.log("info", "Litp is not up after {0} seconds"
                         .format(elapsed_sec))
            except:
                self.log("error", "Unexpected Exception: {0}"
                         .format(sys.exc_info()[0]))

            time.sleep(10)
            elapsed_sec += 10

        if not m_nodes_up:
            self.log("error", "Node {0} is not up in last {1} seconds."
                     .format(self.mn_nodes[0], str(max_duration)))

        # Wait for NTP to resync times so that mco works again.
        return m_nodes_up

    @attr('manual-test')
    def test_01_n_restore_passes_if_restore_is_running(self):
        """
        Description:
            Test that ensures the restore task passes if it finds a filesystem
            currently restoring
        Steps:
            1. create an sfs-cache
            2. create a large fs through litp
            3. create an sfs-export
            4. create and run plan
            5. make changes to the fs on the sfs
            6. run create_snapshot
            7. make changes to the fs on the sfs
            8. check the sfs for the filesystems and cache
            9. remove the export
            10. offline the filesystem
            11. issue a restore (rollback) directly on the sfs
            12. run restore_snapshot
            13. ensure the plan passes
            14. Check the sfs for the export and filesystem
        Results:
            restore_snapshot should pass
        """
        self.remove_snapshots()
        test_number = "_test01"
        file_system1 = "10840-fs1_a" + test_number
        file_systems = [file_system1]
        path1 = "/vx/" + file_system1
        file_path = path1 + "/testfile_1.txt"
        cache_name = "10840_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem1 = self.sfs_pools[0] + '/file_systems/fs1_10840_a' \
                                            + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props1 = "path=" + "'" + path1 + "' " + \
                                "size=" + "'" "40G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "50" "' "
        snapshot_name = "L_" + file_system1 + "_"
        sfs_export = sfs_filesystem1 + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem1 + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

        # 1. create an sfs-cache
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml,
                         add_to_cleanup=False)
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem1,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props1,
                         xml_path=sfs_filesystem_xml,
                         add_to_cleanup=False)
        # 3. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml,
                         add_to_cleanup=False)

        try:
            # 4. Create and run the plan
            self.create_plan()
            # 5. make changes to the fs on the sfs
            self.write_to_node(file_path)
            # 6. run create_snapshot
            self.create_snapshot()
            # 7. make changes to the fs on the sfs
            self.write_to_node(file_path)
            # 8. check the sfs
            self.check_sfs(file_systems, path1)
            # 9. remove the export
            self.delete_sfs_shares(self.nas_server, path1)
            # 10. offline the filesystem
            self.offline_fs(file_system1)
            # 11. issue a restore (rollback) directly on the sfs
            self.restore_fs(file_system1, snapshot_name)
            # 12. run restore_snapshot
            self.execute_cli_restoresnapshot_cmd(self.ms_node)
            # 13. ensure the plan passes
            self._verify_restore_snapshot_completes()
            # 14. Check the sfs for the export and filesystem
            self.check_sfs(file_systems, path=path1)

        finally:
            self.remove_snapshots()
            self.clean_sfs(file_systems, path=path1)
