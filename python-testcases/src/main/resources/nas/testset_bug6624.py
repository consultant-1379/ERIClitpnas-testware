"""
@copyright: Ericsson Ltd
@since:     November 2014
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-6624
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
import test_constants
from xml_utils import XMLUtils


class Bug6624(GenericTest):
    """
    LITPCDS-6624:
            In a dual stack scenario i.e an nfs-service that has ipv4/ipv6
            addresses defined the NAS plugin should first attempt to mount
            over ipv4 if fail then ipv6.
    """

    def setUp(self):
        """Run before every test """
        super(Bug6624, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.rhel_server = self.get_rhel_server_node_filenames()[0]
        self.rhel_server_ipv4 = self.get_node_att(self.rhel_server, "ipv4")
        self.rhel_server_ipv6 = self.get_node_att(self.rhel_server, "ipv6")

    def tearDown(self):
        """Run after every test"""
        super(Bug6624, self).tearDown()

    def export_validate_xml(self, path, file_name):
        """
        Description
            Exports the created item to xml file and Validates the xml file
        Actions:
            1: run export command on item path
            2: validate the xml file
        """
        # EXPORT CREATED PROFILE ITEM
        self.execute_cli_export_cmd(self.ms_node, path, file_name)
        # validate xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, stderr, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], stdout)
        self.assertEqual(0, exit_code)
        self.assertEqual([], stderr)

    def load_xml(self, path, file_name):
        """
        Description
            Loads the created xml file and Validates the xml file
        Actions:
            1. Loads the xml
            2. Expects an error
        """
        _, stderr, _ = self.execute_cli_load_cmd(
            self.ms_node, path, file_name, expect_positive=False)
        self.assertTrue(self.is_text_in_list("ItemExistsError ", stderr))

    def check_mount_in_fstab(self, item2grep, mnt_path, node):
        """
        Ensures mounted filesystem entry in fstab
        """
        cmd = self.storage.get_mount_list_cmd(
            grep_item=item2grep)
        out, err, ret_code = self.run_command(node, cmd)
        # expect an output
        self.assertNotEqual([], out)
        # expect no error
        self.assertEqual([], err)
        # expect the return code to equal 0
        self.assertEqual(0, ret_code)
        # expect mount point string
        self.assertTrue(self.is_text_in_list(
            mnt_path, out))

    @attr('all', 'revert', 'bug6624', 'bug6624_tc01')
    def test_01_p_non_sfs_unmanaged_mount_on_ms_over_ipv4(self):
        """
        Description:
        Mount a non-SFS unmanaged mount in a dual stack scenario where
        only the ipv4 address of the node is an allowed client of the
        export. Check the mount has been mounted over ipv4 address
        Steps:
        Actions:
        1. Create nfs-service with ipv4 and ipv6 addresses,
        2. Create nfs-mount and inherit to the node,
        3. Check plan finished with success
        4. Check mount is successful and ipv4 address is in /etc/fstab
        5. Check property "mount_ip" on inherited nfs-mount value is ipv4
        Results:
            Create plan should succeed and assert that the fs is mounted
            and that property has been updated.
        """
        test_number = "_test1"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        nfs_service = sfsservice_url[0] + '/sp1_6624' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_6624' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_6624' + test_number

        nfs_service_props = "name='nfs1'" + \
                            " ipv4address=" + "'" \
                            + self.rhel_server_ipv4 + "'" \
                            + " ipv6address=" + "'" \
                            + self.rhel_server_ipv6 + "'"

        unmanaged_nfs_mount_props = \
            "export_path=" + test_constants.MOUNT_PATH_NAME6_IPV4 + \
            " network_name='mgmt' " + \
            "provider='nfs1' " + \
            "mount_options='soft' " + \
            "mount_point='/6624_test1' "

        # 1. Create non-SFS unmanaged mounts on MS
        self.execute_cli_create_cmd(
            self.ms_node, nfs_service, "nfs-service", nfs_service_props)
        # xml test
        self.export_validate_xml(nfs_service, "xml_bug6624.xml")
        self.load_xml(sfsservice_url[0], "xml_bug6624.xml")

        # /test1 mount is read/write
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_bug6624.xml")
        self.load_xml(nfs_mount_xml, "xml_bug6624.xml")

        # Mount filesystem on the Node 1
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        # ensure plan was successful
        self.assertTrue(completed_successfully)

        # Step 4: Assert mounted file system is no longer in /etc/fstab
        self.check_mount_in_fstab(test_constants.MOUNT_PATH_NAME6_IPV4,
                                  test_constants.MOUNT_PATH_NAME6_IPV4,
                                  self.ms_node)

        # Step 7.Check /test mount directory is present
        self.assertTrue(self.remote_path_exists(
            self.ms_node, '/6624_test1', expect_file=False))

    @attr('all', 'revert', 'bug6624', 'bug6624_tc02')
    def test_02_p_non_sfs_unmanaged_mount_on_ms_over_ipv6(self):
        """
        Description:
        Mount a non-SFS unmanaged mount in a dual stack scenario where
        only the ipv6 address of the node is an allowed client of the
        export. Check the mount has been mounted over ipv6 address
        Steps:
        Actions:
        1. Create nfs-service with ipv4 and ipv6 addresses,
        2. Create nfs-mount and inherit to the node,
        3. Check plan finished with success
        4. Check mount is successful and ipv6 address is in /etc/fstab
        5. Check property "mount_ip" on inherited nfs-mount value is ipv6
        Results:
            Create plan should succeed and assert that the fs is mounted
            and that property has been updated.
        """
        test_number = "_test2"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        nfs_service = sfsservice_url[0] + '/sp1_6624' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_6624' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_6624' + test_number

        nfs_service_props = "name='nfs1'" + \
                            " ipv4address=" + "'" \
                            + self.rhel_server_ipv4 + "'" \
                            + " ipv6address=" + "'" \
                            + self.rhel_server_ipv6 + "'"

        unmanaged_nfs_mount_props = \
            "export_path=" + test_constants.MOUNT_PATH_NAME5_IPV6 + \
            " network_name='mgmt' " + \
            "provider='nfs1' " + \
            "mount_options='soft' " + \
            "mount_point='/6624_test2' "

        # 1. Create non-SFS unmanaged mounts on MS
        self.execute_cli_create_cmd(
            self.ms_node, nfs_service, "nfs-service", nfs_service_props)
        # xml test
        self.export_validate_xml(nfs_service, "xml_bug6624.xml")
        self.load_xml(sfsservice_url[0], "xml_bug6624.xml")

        # /test1 mount is read/write
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_bug6624.xml")
        self.load_xml(nfs_mount_xml, "xml_bug6624.xml")

        # Mount filesystem on the Node 1
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        # ensure plan was successful
        self.assertTrue(completed_successfully)

        # Step 4: Assert mounted file system is no longer in /etc/fstab
        self.check_mount_in_fstab(test_constants.MOUNT_PATH_NAME5_IPV6,
                                  test_constants.MOUNT_PATH_NAME5_IPV6,
                                  self.ms_node)

        # Step 7.Check /test mount directory is present
        self.assertTrue(self.remote_path_exists(
            self.ms_node, '/6624_test2', expect_file=False))

    @attr('all', 'revert', 'bug6624', 'bug6624_tc02')
    def test_03_p_non_sfs_unmanaged_mount_dual_ipv_on_ms(self):
        """
        Description:
        Mount a non-SFS unmanaged mount in a dual stack scenario where
        both ipv4/ipv6 address of the node is an allowed client of the
        export. Check the mount has been mounted over ipv4 address as
        this is the first one tried
        Steps:
        Actions:
        1. Create nfs-service with ipv4 and ipv6 addresses,
        2. Create nfs-mount and inherit to the node,
        3. Check plan finished with success
        4. Check mount is successful and ipv4 address is in /etc/fstab
        5. Check property "mount_ip" on inherited nfs-mount value is ipv6
        Results:
            Create plan should succeed and assert that the fs is mounted
            and that property has been updated.
        """
        test_number = "_test3"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        nfs_service = sfsservice_url[0] + '/sp1_6624' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_6624' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_6624' + test_number

        nfs_service_props = "name='nfs1'" + \
                            " ipv4address=" + "'" \
                            + self.rhel_server_ipv4 + "'"\
                            + " ipv6address=" + "'" \
                            + self.rhel_server_ipv6 + "'"

        unmanaged_nfs_mount_props = \
            "export_path=" + test_constants.MOUNT_PATH_NAME7_DUAL + \
            " network_name='mgmt' " + \
            "provider='nfs1' " + \
            "mount_options='soft' " + \
            "mount_point='/6624_test3' "

        # 1. Create non-SFS unmanaged mounts on MS
        self.execute_cli_create_cmd(
            self.ms_node, nfs_service, "nfs-service", nfs_service_props)
        # xml test
        self.export_validate_xml(nfs_service, "xml_bug6624.xml")
        self.load_xml(sfsservice_url[0], "xml_bug6624.xml")

        # /test1 mount is read/write
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_bug6624.xml")
        self.load_xml(nfs_mount_xml, "xml_bug6624.xml")

        # Mount filesystem on the Node 1
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # Step 4: Assert mounted file system is no longer in /etc/fstab
        self.check_mount_in_fstab(test_constants.MOUNT_PATH_NAME7_DUAL,
                                  test_constants.MOUNT_PATH_NAME7_DUAL,
                                  self.ms_node)

        # Step 7.Check /test mount directory is present
        self.assertTrue(self.remote_path_exists(
            self.ms_node, '/6624_test3', expect_file=False))
