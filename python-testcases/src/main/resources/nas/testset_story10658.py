"""
@copyright: Ericsson Ltd
@since:     November 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-10658
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from xml_utils import XMLUtils
import test_constants
import time
import socket
import exceptions
import sys


class Story10658(GenericTest):
    """
    LITPCDS-10658:
        As a Litp user I want the NAS plugin to ignore missing
        snapshots when I run "litp restore_snapshot -f"
    """

    def setUp(self):
        """Run before every test"""
        super(Story10658, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.rhcmd = RHCmdUtils()
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story10658, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story10658.xml"):
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

    def restore_snapshot(self, args='', expect_positive=True,
                         error_message=None):
        """
        Restore the snapshot
        """
        if expect_positive:
            # 1. Execute restore_snapshot command
            self.execute_cli_restoresnapshot_cmd(self.ms_node, args)

        else:
            # 1. Execute restore_snapshot command
            _, stderr, _ = self.execute_cli_restoresnapshot_cmd(
                self.ms_node, args, expect_positive=False)
            self.assertTrue(stderr, error_message)

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
                out, _, ret_code = self.execute_cli_show_cmd(
                    self.ms_node, "/deployments"
                )

                self.assertEqual(0, ret_code)
                self.assertNotEqual([], out)

                if self.is_text_in_list("collection-of-deployment", out):
                    self.log("info", "Litp is up")
                    litp_up = True
                    break
                else:
                    self.log("info", "Litp is not up.")

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
        time.sleep(60)
        return m_nodes_up

    @attr('manual-test')
    def test_01_p_restore_snapshot_of_sfs_filesystems_with_f_option(self):
        """
        Description:
            Test that ensures we can restore sfs filesystems
        Steps:
        1. create an sfs-cache
        2. create an sfs-filesystem with a size of 10G and snap_size of 10
        3. create an sfs-filesystem with a size of 10G and snap_size of 10
        4. create an sfs-filesystem with a size of 10G and snap_size of 10
        5. create and run plan
        6. run create_snapshot
        7. check the sfs
        8. delete the snapshots for fs1 and fs2 on the sfs
        9. run restore_snapshot
        10. ensure the plan fails
        11. run restore_snapshot with the -f option
        12. ensure plan runs with success
        Results:
            Restore_snapshot should run when the -f option is used
        """
        self.remove_all_snapshots(node=self.ms_node)
        test_number = "_test01"
        file_system1 = "10658-fs1_a" + test_number
        file_system2 = "10658-fs1_b" + test_number
        file_system3 = "10658-fs1_c" + test_number
        file_systems = [file_system1, file_system2, file_system3]
        path1 = "/vx/" + file_system1
        path2 = "/vx/" + file_system2
        path3 = "/vx/" + file_system3
        paths = [path1, path2, path3]
        cache_name = "10658_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_10658'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem1 = self.sfs_pools[0] + '/file_systems/fs1_10658_a' \
                                            + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_10658_b' \
                                            + test_number
        sfs_filesystem3 = self.sfs_pools[0] + '/file_systems/fs1_10658_c' \
                                            + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props1 = "path=" + "'" + path1 + "' " + \
                                "size=" + "'" "10G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "path=" + "'" + path3 + "' " + \
                                "size=" + "'" "10G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        snapshot_name1 = "L_" + file_system1 + "_"
        snapshot_name2 = "L_" + file_system2 + "_"

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
        # 3. create an sfs-filesystem fs2
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)
        # 4. create an sfs-filesystem fs3
        self.create_item(item_path=sfs_filesystem3,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props3,
                         xml_path=sfs_filesystem_xml)
        try:
            # 5. Create and run the plan
            self.create_plan()
            # 6. run create_snapshot
            self.create_snapshot()
            # 7. check the sfs
            self.check_sfs(file_systems, cache_name=cache_name)
            # 8. delete the snapshots for fs1 and fs2 on the sfs
            self.delete_sfs_snapshot(self.nas_server, snapshot_name1,
                                     file_system1)
            self.delete_sfs_snapshot(self.nas_server, snapshot_name2,
                                     file_system2)
            # 9. run restore_snapshot
            self.restore_snapshot()
            # 10. ensure the plan fails
            self.assertTrue(self.wait_for_plan_state(
                            self.ms_node, test_constants.PLAN_FAILED,
                            self.timeout_mins))
            # 11. run restore_snapshot with the -f option
            self.restore_snapshot(args="-f")
            # 12. ensure plan runs with success
            self._verify_restore_snapshot_completes()

        finally:
            self.remove_all_snapshots(node=self.ms_node)
            self.clean_sfs(file_systems, paths=paths)
