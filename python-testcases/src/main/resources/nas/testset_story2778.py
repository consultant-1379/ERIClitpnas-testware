"""
@copyright: Ericsson Ltd
@since:     July 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-2778
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
from xml_utils import XMLUtils
import test_constants
import time
import socket
import exceptions
import sys


class Story2778(GenericTest):
    """
    LITPCDS-2778:
        As a LITP User I want to restore to a SFS snapshot that I h
        ave already taken, so that my system is in a known good state.
    """

    def setUp(self):
        """Run before every test"""
        super(Story2778, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.ms_ip_address = self.get_node_att(self.ms_node, 'ipv4')
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')
        self.node2_ip_address = self.get_node_att(self.mn_nodes[1], 'ipv4')
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        self.nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                      "storage", True)
        self.nfs_mount_xml = self.nfsmount_url[0] + '/nfs_mounts'
        self.rhcmd = RHCmdUtils()
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story2778, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story2778.xml"):
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
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                        test_constants.PLAN_COMPLETE, self.timeout_mins))

            else:
                # 2. Verify that the create snapshot plan fails
                self.assertFalse(self.wait_for_plan_state(self.ms_node,
                        test_constants.PLAN_COMPLETE, self.timeout_mins))

        else:
            # 1. Execute create_snapshot command
            _, stderr, _ = self.execute_cli_createsnapshot_cmd(
                self.ms_node, args=args, expect_positive=False)
            self.assertTrue(stderr, error_message)

    def remove_snapshots(self, cleanup=True):
        """
        Deletes all snapshots
        """
        timeout_mins = 3
        snapshot_url = self.find(self.ms_node, "/snapshots",
                              "snapshot-base", assert_not_empty=False)

        list_of_snaps = []
        for snap in snapshot_url:
            if snap == "/snapshots/snapshot":
                self.execute_cli_removesnapshot_cmd(self.ms_node,
                                                    add_to_cleanup=cleanup)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, timeout_mins))

            else:
                snapshot_name = snap.split("/snapshots/").pop()
                list_of_snaps.append(snapshot_name)

        if list_of_snaps:
            for snap in list_of_snaps:
                args = "-n " + snap
                self.execute_cli_removesnapshot_cmd(self.ms_node, args=args,
                                                    add_to_cleanup=cleanup)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, timeout_mins))

    def inherit(self, path, source_path):
        """
        Method that runs the "inherit" command given passed path and
        source path
        """
        self.execute_cli_inherit_cmd(self.ms_node, path, source_path)

    def restore_snapshot(self, expect_positive=True, error_message=None):
        """
        Restore the snapshot
        """
        if expect_positive:
            # 1. Execute restore_snapshot command
            self.execute_cli_restoresnapshot_cmd(self.ms_node)

        else:
            # 1. Execute restore_snapshot command
            _, stderr, _ = self.execute_cli_restoresnapshot_cmd(
                self.ms_node, expect_positive=False)
            self.assertTrue(stderr, error_message)

    def write_to_node(self, file_path, node=None, su_root=False, sfs=False):
        """
        Write a file to a mount point on a node
        """
        node = node or self.ms_node
        file_contents = ["one", "two", "three",
                            "four", "five", "six"]

        if sfs:
            size_kb = "1024"
            node = self.nas_server
            cmd = \
            "/bin/dd if=/dev/urandom of={0} bs={1} \
                count={2}".format(file_path, size_kb, size_kb)

            self.run_command(node, cmd, username=self.sfs_server_user,
                             password=self.sfs_server_pw)
        else:
            self.assertTrue(self.create_file_on_node(
                node, file_path, file_contents, su_root))

    def copy_data(self, path, file_path, node=None):
        """
        Copy data to new files on a node
        """
        node = node or self.nas_server
        files = ["/a.dat", "/b.dat", "/c.dat"]

        for fil in files:
            fil = path + fil
            copy_cmd = "cp {0} {1}".format(file_path, fil)
            self.run_command(node, copy_cmd,
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
    def test_01_p_restore_snapshot_of_sfs_filesystems(self):
        """
        @tms_id: litpcds_2778_tc01
        @tms_requirements_id: LITPCDS-2778
        @tms_title: Restore snapshot of sfs filesystems
        @tms_description: Test that ensures we can restore sfs filesystems
        @tms_test_steps:
            @step: Create an sfs-cache
            @result: sfs-cache created
            @step: Create an sfs-filesystem with a size of 10G and
            snap_size of 10
            @result: sfs-filesystem created
            @step: Create an sfs-filesystem with a size of 10G and
            snap_size of 10
            @result: sfs-filesystem created
            @step: Create an sfs-filesystem with a size of 10G and
            snap_size of 10
            @result: sfs-filesystem created
            @step: Create an sfs-filesystem with a size of 10G
            @result: sfs-filesystem created
            @step: create an sfs-export for fs1 with the ms as an
            allowed_client
            @result: sfs-export created
            @step: create an sfs-export for fs2 with the n1 as an
            allowed_client
            @result: sfs-export created
            @step: create an nfs-mount on the ms
            @result: nfs-mount created
            @step: inherit the nfs-mount on to the ms
            @result: nfs-mount inherited
            @step: create and run plan
            @result: Plan is running
            @step: create a file on the ms mount point
            @result: File is created
            @step: run create_snapshot
            @result: snapshot is created
            @step: check the sfs
            @result: sfs is checked
            @step: create another file on the ms mount point
            @result: file is created
            @step: update the allowed clients of the second export
            @result: clients are updated
            @step: create an export for fs3 with n1 in the allowed_clients
            @result: export is created
            @step: Add snap_size and cache_name to fs4
            @result: Properties added to fs4
            @step: mount fs4 to node1
            @result: mount is successful
            @step: manually create a snapshot for fs4
            @result: snapshot is created
            @step: create and run plan
            @result: Plan executes successfully
            @step: run restore_snapshot and ensure plan runs with success
            @result: The above is successful
            @step: ensure the changes to exports and filesystems are
            reverted correctly on the sfs and in the model
            @result: The above is successful
            @step: ensure the cache is not deleted on the sfs
            @result: cache is not deleted
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test01"
        file_system1 = "2778-fs1_a" + test_number
        file_system2 = "2778-fs1_b" + test_number
        file_system3 = "2778-fs1_c" + test_number
        file_system4 = "2778-fs1_d" + test_number
        file_systems = [file_system1, file_system2, file_system3,
                        file_system4]
        path1 = "/vx/" + file_system1
        path2 = "/vx/" + file_system2
        path3 = "/vx/" + file_system3
        path4 = "/vx/" + file_system4
        paths = [path1, path2, path3]
        cache_name = "2778_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2778'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem1 = self.sfs_pools[0] + '/file_systems/fs1_2778_a' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2778_b' \
                 + test_number
        sfs_filesystem3 = self.sfs_pools[0] + '/file_systems/fs1_2778_c' \
                 + test_number
        sfs_filesystem4 = self.sfs_pools[0] + '/file_systems/fs1_2778_d' \
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
        sfs_filesystem_props4 = "path=" + "'" + path4 + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props5 = "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "'"
        sfs_export1 = sfs_filesystem1 + '/exports/ex1_2778_a' + test_number
        sfs_export2 = sfs_filesystem2 + '/exports/ex1_2778_b' + test_number
        sfs_export3 = sfs_filesystem3 + '/exports/ex1_2778_c' + test_number
        sfs_export_xml1 = sfs_filesystem1 + '/exports'
        sfs_export_xml2 = sfs_filesystem2 + '/exports'
        sfs_export_xml3 = sfs_filesystem3 + '/exports'
        sfs_export_props1 = "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "'"
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "'"
        sfs_export_props3 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.ms_ip_address + "'"
        sfs_export_props4 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "'"
        nfs_mount = self.nfsmount_url[0] + \
                    '/nfs_mounts/nm1_2778' + test_number
        nfs_mount2 = self.nfsmount_url[0] + \
                     '/nfs_mounts/nm1_2778_b' + test_number
        nfs_mount_xml = self.nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props1 = "export_path=" "'" + path1 + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/2778_test1" + "'"
        nfs_mount_props2 = "export_path=" "'" + path2 + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/2778_test1_b" + "'"
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_2778' + test_number
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_2778' + \
                           test_number
        file_path1 = "/2778_test1/testfile_1.txt"
        file_path2 = "/2778_test1/testfile_2.txt"
        snapshot_name = "L_" + file_system4 + "_"

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
        # 5. create an sfs-filesystem fs4
        self.create_item(item_path=sfs_filesystem4,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props4,
                         xml_path=sfs_filesystem_xml)
        # 6. create an sfs-export
        self.create_item(item_path=sfs_export1,
                         item_type="sfs-export",
                         item_props=sfs_export_props1,
                         xml_path=sfs_export_xml1)
        # 7. create an sfs-export
        self.create_item(item_path=sfs_export2,
                         item_type="sfs-export",
                         item_props=sfs_export_props2,
                         xml_path=sfs_export_xml2)
        # 8. create an nfs-mount on ms
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props1,
                         xml_path=nfs_mount_xml)
        # 9. inherit mount to node
        self.inherit(path=ms_file_system, source_path=nfs_mount)

        try:
            # 10. Create and run the plan
            self.create_plan()
            # 11. create a file on the ms mount point
            self.write_to_node(file_path1, su_root=True)
            # 12. run create_snapshot
            self.create_snapshot()
            # 13. check the sfs
            self.check_sfs(file_systems, cache_name=cache_name)
            # 14. create another file on the ms mount point
            self.write_to_node(file_path2, su_root=True)
            # 15. update the allowed clients of the second export
            self.update_item(sfs_export2, item_props=sfs_export_props3)
            # 16. create an export for fs3 with n1 in the allowed_clients
            self.create_item(item_path=sfs_export3,
                             item_type="sfs-export",
                             item_props=sfs_export_props4,
                             xml_path=sfs_export_xml3)
            # 17. Add snap_size and cache_name to fs4
            self.update_item(sfs_filesystem4,
                             item_props=sfs_filesystem_props5)
            # 18. mount fs4 to node1
            self.create_item(item_path=nfs_mount2,
                             item_type="nfs-mount",
                             item_props=nfs_mount_props2,
                             xml_path=nfs_mount_xml)
            self.inherit(path=node_file_system, source_path=nfs_mount2)
            # 19. manually create a snapshot for fs4
            self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
            self.create_sfs_snapshot(self.nas_server,
                                     snapshot_name=snapshot_name,
                                     fs_name=file_system4,
                                     cache_name=cache_name)
            # 20. create and run plan
            self.create_plan()
            # 21. run restore_snapshot
            self.restore_snapshot()
            # 22. ensure plan runs with success
            self._verify_restore_snapshot_completes()
            # 23. ensure the changes to exports and filesystems are
            #    reverted correctly on the sfs and in the model
            self.assertTrue(self.remote_path_exists(self.ms_node, file_path1))
            self.assertFalse(self.remote_path_exists(self.ms_node, file_path2))
            # 24. ensure the cache is not deleted on the sfs
            self.check_sfs(file_systems, cache_name=cache_name)

        finally:
            self.delete_sfs_snapshot(self.nas_server,
                                     snapshot_test=snapshot_name,
                                     fs_test=file_system4)
            self.remove_snapshots()
            self.clean_sfs(file_systems, paths=paths)

    def obsolete_02_n_manually_remove_a_snapshot_before_restore(self):
        """
        Description:
            Test that manually removes an sfs snapshot before we run a restore
            This test is being made obsolete as the functionality is
            now changed to it's own task when the user runs
            restore_snapshot. This was brought in with story 10947.
        Steps:
        1. create an sfs-cache
        2. create an sfs-filesystem with a size of 10G and snap_size of 10
        3. create an sfs-filesystem with a size of 20G and snap_size of 10
        4. Create and run the plan
        5. Ensure filesystem are created
        6. run create_snapshot
        7. Check the sfs
        8. remove a snapshot directly on the sfs for one of the filesystems
        9. run restore_snapshot and ensure the correct error is thrown
        Results:
            Restore_snapshot plan should throw an PluginError
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test02"
        file_system = "2778-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "2778-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "2778_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2778'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2778' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2778' \
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
        error_message = 'Restore snapshot failed: SFS Snapshot "' + \
                        snapshot_name + '" for filesystem "' + \
                        file_system + '" does not exist on the SFS'

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
            # 9. run restore_snapshot and ensure the correct error is thrown
            self.restore_snapshot(expect_positive=False,
                                  error_message=error_message)

        finally:
            self.remove_snapshots()
            self.clean_sfs(file_systems)

    def obsolete_03_n_ensure_restore_fails_when_cache_is_full(self):
        """
        Description:
            Test that fills up an sfs cache before running restore_snapshot
            This test is being made obsolete as the functionality is
            now changed to it's own task when the user runs
            restore_snapshot. This was brought in with story 10947.
        Steps:
        1. create an sfs-cache
        2. create 2 sfs-filesystems with sizes 10M and 20M, snap_sizes of 10
        3. Create and run the plan
        4. Ensure filesystems are created
        5. run create_snapshot
        6. Check the sfs
        7. copy files to the sfs to fill up the cache
        8. Wait for cache to fill
        9. run restore_snapshot and ensure the
           correct error is thrown
        Results:
            Restore_snapshot plan should throw an PluginError
        """
        self.remove_snapshots()
        test_number = "_test03"
        file_system = "2778-fs1" + test_number
        file_system2 = "2778-fs1_b" + test_number
        file_systems = [file_system, file_system2]
        path = "/vx/" + file_system
        path2 = "/vx/" + file_system2
        file_path = path + "/testfile_3.dat"
        file_path2 = path2 + "/testfile_3_b.dat"
        cache_name = "2778_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2778'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2778' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2778_b' \
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
        error_message = 'Restore snapshot failed: Snapshot(s) corrupted ' \
                        'because no space is available on SFS ' \
                        'cache "' + cache_name + '".'

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
            self.write_to_node(file_path, sfs=True)
            self.write_to_node(file_path2, sfs=True)
            self.copy_data(path=path, file_path=file_path)
            self.copy_data(path=path2, file_path=file_path2)
            # 8. Wait for cache to fill
            self.assertTrue(self.cache_full(cache_name))
            # 9. run restore_snapshot and ensure the
            # correct error is thrown
            self.restore_snapshot(expect_positive=False,
                                  error_message=error_message)

        finally:
            self.remove_snapshots()
            self.clean_sfs(file_systems)
