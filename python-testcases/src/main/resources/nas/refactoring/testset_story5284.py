"""
@copyright: Ericsson Ltd
@since:     April 2014
@author:    ekenmon, etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-5284
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
import test_constants
from xml_utils import XMLUtils

MOUNTED_FS_NAME = 'file_system4'
MOUNTED_FS_NAME2 = 'file_system5'
MOUNTED_FS_NAME3 = 'ro_unmanaged'
MOUNTED_FS_NAME4 = 'rw_unmanaged'
MOUNT_PATH_NAME = '/vx/ossrc1-file_system4'
MOUNT_PATH_NAME2 = '/vx/ossrc1-file_system5'
MOUNT_PATH_NAME3 = '/home/admin/nfs_share_dir/ro_unmanaged'
MOUNT_PATH_NAME4 = '/home/admin/nfs_share_dir/rw_unmanaged'


class Story5284(GenericTest):
    """
    LITPCDS-5284:
        The NAS plugin is used to mount or unmount a filesystem in the
         fstab with value provided by the user
    """

    def setUp(self):
        """Run before every test """
        super(Story5284, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.rhel_server = self.get_rhel_server_node_filenames()[0]
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.server_name = self.get_node_att(self.nas_server, "nodetype")
        self.sfs_server_ip = self.get_node_att(self.nas_server, "ipv4")
        self.rhel_server_ip = self.get_node_att(self.rhel_server, "ipv4")

    def tearDown(self):
        """Run after every test"""
        super(Story5284, self).tearDown()

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

    def check_mount_in_fstab(self, item2grep, mnt_path, node, frequency=1):
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

        self.assertTrue(len(out) == frequency)

    def check_mount_not_in_fstab(self, item2grep, node):
        """
        Ensures previously mounted filesystem is not in fstab
        """
        cmd = self.storage.get_mount_list_cmd(
            grep_item=item2grep)
        out, err, ret_code = self.run_command(node, cmd)
        # expect an output
        self.assertEqual([], out)
        # expect no error
        self.assertEqual([], err)
        # expect the return code to equal 0
        self.assertEqual(1, ret_code)

    def create_plan(self):
        """
        Method to create & run plan, checks successful exe
        """
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        # ensure plan was successful
        self.assertTrue(completed_successfully, "Plan was not successful")

    def check_permissions(self, node, file_path='/vx/ossrc1-file_system4'):
        """
        Checks permissions on file
        """
        cmd = r"(/usr/bin/stat " + file_path + " | /bin/sed -n '/^Access: " \
              r"(/{s/Access: (\([0-9]\+\).*$/\1/;p}')"
        out, err, rc = self.run_command(node, cmd)
        self.assertEqual(0, rc)
        self.assertEqual([], err)
        self.assertEqual(['0755'], out)

    def __get_non_sfs_path_name(self):
        """
        If NFS ip address is already defined in model returns
        values from model for selected IP. Otherwise creates the item
        nfs service.

        Returns:
           str, str. The litp path to the NFS service and the service name.
        """
        nfs_existing_path = self.find_nfs_path_by_ip(self.ms_node,
                                                     self.rhel_server_ip)

        if nfs_existing_path:
            nfs_service = nfs_existing_path
            nfs_name = self.get_props_from_url(self.ms_node, nfs_service,
                                               'name')
        else:
            sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                       "storage-provider-base",
                                       rtn_type_children=False, find_refs=True)
            nfs_service = sfsservice_url[0] + '/sp1_5284'
            nfs_name = 'nfs1'
            nfs_service_props = "name='{0}' ".format(nfs_name) + \
                                "ipv4address=" + "'" + \
                                self.rhel_server_ip + "'"
            # 1. Create non-SFS unmanaged mounts on MS
            self.execute_cli_create_cmd(
                self.ms_node, nfs_service, "nfs-service", nfs_service_props)
            # xml test
            self.export_validate_xml(nfs_service, "xml_story5436.xml")
            self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        return nfs_service, nfs_name

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc01', 'cdb_priority1')
    def test_01_p_create_sfs_unmanaged_mounts_ms(self):
        """
        Now covers litpcds_5985_tc01
        #tms_id: litpcds_5284_tc01
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create sfs unmanaged mounts on the ms
        #tms_description: Test the creation of SFS unmanaged mount on
        the MS
        #tms_test_steps:
            #step: Create sfs service
            #result: sfs service is created
            #step: Create read only nfs-mount on the ms
            #result: nfs-mount is created
            #step: Create read-writeable nfs-mount on the ms
            #result: nfs-mount is created
            #step: Export NAS items to an xml file and check this file
            against XSD
            #result: Export is successful
            #step: create and run plan
            #result: plan is running
            #result: plan is successful
            #step: Assert file system 1 has been mounted in /etc/fstab
            #result: file system is mounted
            #step: Assert file system 2 has been mounted in /etc/fstab
            #result: file system is mounted
            #step: Check that the permissions on the mount are 0755
            #result: Mount permissions are as expected
            #step: As root user, write in the read only mount
            #result: Assert that this is not possible
            #step: As root user, write in the read/writable mount
            #result: Assert that this is successful
            #step: Remove file_system and mount
            #result: File system and mount removed
            #step: Ensure filesystem and directories have been removed from
                the system
            #result: The filesystem and directories have been removed
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test01"
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)

        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        ms_file_system = ms_url[0] + '/nm1_5284' + test_number
        ms_file_system2 = ms_url[0] + '/nm2_5284' + test_number

        sfs_unmanged_service_props = "name=" + "'" + self.server_name + "'"

        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider='virtserv1' " + \
                          "mount_point='/5284_test1' "
        nfs_mount_props2 = "export_path='/vx/ossrc1-file_system4' " + \
                           "network_name='mgmt' " + \
                           "provider='virtserv1' " + \
                           "mount_point='/5284_test1b' "

        self.log('info', "1. Create SFS unmanaged mounts on MS")
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_unmanged_service_props)
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount", nfs_mount_props2)
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system2, nfs_mount2)

        self.log('info', "2. Create and run the plan")
        self.create_plan()

        self.log('info', "3. Assert filesystems have been mounted in "
                             "/etc/fstab")
        self.check_mount_in_fstab(MOUNTED_FS_NAME,
                                  MOUNT_PATH_NAME, self.ms_node, frequency=2)

        self.log('info', "4. Check directory permissions")
        self.check_permissions(self.ms_node, file_path='/5284_test1')
        self.check_permissions(self.ms_node, file_path='/5284_test1b')

        self.log('info', "5. Write to mounted dirs as root")
        filepath = '/5284_test1/my_file.txt'
        file_contents_ls = ['test_write_contents']
        self.assertFalse(self.create_file_on_node(
            self.ms_node, filepath, file_contents_ls, su_root=True))

        filepath = '/5284_test1b/my_file.txt'
        file_contents_ls = ['test_write_contents']
        self.assertFalse(self.create_file_on_node(
            self.ms_node, filepath, file_contents_ls, su_root=True))

        self.log('info', "6. Remove file system and mount")
        self.execute_cli_remove_cmd(self.ms_node, ms_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)
        self.execute_cli_remove_cmd(self.ms_node, ms_file_system2)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount2)

        self.log('info', "7. Create and run plan")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        self.assertTrue(completed_successfully, "Plan was not successful")

        self.log('info', "8. Ensure filesystem and directories have been "
                         "removed from the system")
        self.check_mount_not_in_fstab(test_constants.MOUNT_PATH_NAME1,
                                      self.ms_node)

        self.remote_path_exists(self.ms_node, '/5284_test1', expect_file=False)
        self.remote_path_exists(self.ms_node, '/5284_test1b',
                                expect_file=False)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc02', 'cdb_priority1')
    def obsolete_02_p_create_sfs_unmanaged_mounts_nodes(self):
        """
        Merged with
        test_03_p_create_sfs_unmanaged_mnts_nodes_in_diff_directories.
        Now covers litpcds_5284_tc07
        #tms_id: litpcds_5284_tc02
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create sfs unmanaged mounts on each peer node
        #tms_description: Test the creation of SFS unmanaged mounts on
        the peer nodes
        #tms_test_steps:
            #step: create sfs-service
            #result: sfs-service is created
            #step: create read only sfs unmanaged nfs-mount with
            mount_point='/a/b/c/5284_test2
            #result: nfs-mount is created
            #step: create read writable sfs unmanaged nfs-mount with
            mount_point='/a/b/c/5284_test2_b
            #result: nfs-mount is created
            #step: create and run plan
            #result: Plan is running
            #step: Assert file system has been mounted on node1 /etc/fstab
            #result: file system has been mounted
            #step: Assert file system has been mounted on node2 /etc/fstab
            #result: file system has been mounted
            #step: Verify correct permissions are set for each mount
            #result: Correct permissions are set
            #step: Attempt to write to the read only mount as root
            #result: This is not possible. (Assert false)
            #step: Attempt to write to the writable mount as root
            #result: This is not possible. (Assert true)
            #step: Remove file_system and mount
            #result: File system and mount removed
            #step: Ensure filesystem and directories have been removed from
                the system
            #result: The filesystem and directories have been removed
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc03')
    def test_03_p_create_sfs_unmanaged_mnts_nodes_in_diff_directories(self):
        """
        #tms_id: litpcds_5284_tc03
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create sfs unmanaged mounts in different directories
        #tms_description: Test the creation of SFS unmanaged mounts on
        each node in different directories.
        Covers litpcds_5284_tc02 and litpcds_5284_tc07.
        #tms_test_steps:
            #step: create sfs-service under infrastructure
            #result: sfs-service is created
            #step: create sfs unmanaged nfs-mount with
            mount_point='/a/b/c/5284_test3'
            #result: nfs-mount is created
            #step: create read writable sfs unmanaged nfs-mount with
            mount_point='/a/b/c/5284_test2_b
            #result: nfs-mount is created
            #step: create and run plan
            #result: Plan is running
            #step: Assert file system has been mounted on node1 /etc/fstab
            #result: file system has been mounted
            #step: Assert file system has been mounted on node2 /etc/fstab
            #result: file system has been mounted
            #step: Verify correct permissions are set for each mount
            #result: Correct permissions are set
            #step: Write to the read only mount as root
            #result: This will not be possible. (Assert false)
            #step: Write to the writable mount as root
            #result: This will be possible. (Assert true)
            #step:  Remove file system and mount
            #result: File system and mount removed
            #step: Create and run plan.
            #result: Plan created
            #step: Ensure filesystem and directories have been removed
                   from the system.
            #result: Filesystem and directories removed successfully.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_num = "_test03"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                               "storage", True)

        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_num
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_num
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_num

        file_system1_n1 = nodes_url[0] + '/file_systems/nm1_5284' + test_num
        file_system2_n1 = nodes_url[0] + '/file_systems/nm2_5284' + test_num
        file_system1_n2 = nodes_url[1] + '/file_systems/nm1_5284' + test_num
        file_system2_n2 = nodes_url[1] + '/file_systems/nm2_5284' + test_num

        sfs_unmanged_service_props = "name='{0}'".format(self.server_name)

        nfs_mount_props1 = "export_path='/vx/ossrc1-file_system5' " + \
                           "network_name='mgmt' " + \
                           "provider='virtserv1' " + \
                           "mount_point='/a/b/c/5284_test3' "

        nfs_mount_props2 = "export_path='/vx/ossrc1-file_system5' " + \
                           "network_name='mgmt' " + \
                           "provider='virtserv1' " + \
                           "mount_point='/5284_test3' "

        self.log('info', '# 1. Create SFS unmanaged mounts on node')
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_unmanged_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        # Create first NFS mount
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props1)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount", nfs_mount_props2)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system1_n1, nfs_mount)

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system2_n1, nfs_mount2)

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system1_n2, nfs_mount)

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system2_n2, nfs_mount2)

        self.log('info', ' # 2. Create and run plan')
        self.create_plan()

        self.log('info', '# 3. Assert file system 2 has been mounted in '
                         '/etc/fstab')
        self.check_mount_in_fstab(MOUNTED_FS_NAME2,
                                  MOUNT_PATH_NAME2, self.mn_nodes[0],
                                  frequency=2)
        self.check_mount_in_fstab(MOUNTED_FS_NAME2,
                                  MOUNT_PATH_NAME2, self.mn_nodes[1],
                                  frequency=2)

        self.log('info', '# 4. Verify correct permissions are set')
        self.check_permissions(self.mn_nodes[0],
                               file_path='/a/b/c/5284_test3')
        self.check_permissions(self.mn_nodes[0],
                               file_path='/5284_test3')

        self.check_permissions(self.mn_nodes[1],
                               file_path='/a/b/c/5284_test3')
        self.check_permissions(self.mn_nodes[1],
                               file_path='/5284_test3')

        self.log('info', ' # 5. write to mounted dir as root')
        for node in self.mn_nodes:
            filepath = '/a/b/c/5284_test3/my_file2.txt'
            file_contents_ls = ['test_write_contents']
            if self.remote_path_exists(node, filepath):
                self.remove_item(node, filepath, su_root=True)
            self.assertTrue(self.create_file_on_node(
                node, filepath, file_contents_ls, su_root=True))
            self.remove_item(node, filepath, su_root=True)

        for node in self.mn_nodes:
            filepath = '/5284_test3/my_file2.txt'
            file_contents_ls = ['test_write_contents']
            if self.remote_path_exists(node, filepath):
                self.remove_item(node, filepath, su_root=True)
            self.assertTrue(self.create_file_on_node(
                node, filepath, file_contents_ls, su_root=True))
            self.remove_item(node, filepath, su_root=True)

        self.log('info', "# 6. Remove file system and mount")
        self.execute_cli_remove_cmd(self.ms_node, file_system1_n1)
        self.execute_cli_remove_cmd(self.ms_node, file_system1_n2)
        self.execute_cli_remove_cmd(self.ms_node, file_system2_n1)
        self.execute_cli_remove_cmd(self.ms_node, file_system2_n2)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount2)

        self.log('info', "# 7. Create and run plan")
        self.create_plan()

        self.log('info', "# 8. Ensure filesystem and directories have been "
                         "removed from the system")
        for node in self.mn_nodes:
            self.check_mount_not_in_fstab(MOUNTED_FS_NAME2, node)

            self.remote_path_exists(node, '/5284_test3', expect_file=False)
            self.remote_path_exists(node, '/a/b/c/5284_test2',
                                    expect_file=False)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc04', 'cdb_priority1')
    def test_04_p_create_non_sfs_unmanaged_mounts_ms(self):
        """
        Now covers litpcds_5985_tc02
        #tms_id: litpcds_5284_tc04
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create non sfs unmanaged mounts on the ms
        #tms_description: Test the creation of SFS unmanaged mounts on
        the ms
        #tms_test_steps:
            #step: create nfs-service under infrastructure
            #result: nfs-service is created
            #step: create read only unmanaged nfs-mount on the ms
            with mount_point='/5284_test4'
            #result: read only unmanged nfs-mount created
            #step: create read writable unmanaged nfs-mount on the ms
            with mount_point='/5284_test4_b'
            #result: read writable nfs-mount created
            #step: create and run plan
            #result: plan finishes successfully
            #step: Ensure read only mounted filesystem entry is in
            /etc/fstab
            #result: read only mounted filesystem entry is in /etc/fstab
            #step: Ensure read writable mounted filesystem entry is in
            /etc/fstab
            #result: read writable mounted filesystem entry is in /etc/fstab
            #step: Check that each mount has root ownership and 0755
            permissions
            #result: The above is correct
            #step: Assert that an attempt to write to the read only mount
            as root is not possible
            #result: The above assertion is successful
            #step: Assert that an attempt to write to the writable mount
            as root is possible
            #result: The above assertion is successful
            #step: Remove file_system and mount
            #result: File system and mount removed
            #step: Ensure filesystem and directories have been removed from
                the system
            #result: The filesystem and directories have been removed
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test04"
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)

        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)

        _, nfs_name = self.__get_non_sfs_path_name()

        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        ms_file_system = ms_url[0] + '/nm1_5284' + test_number
        ms_file_system2 = ms_url[0] + '/nm2_5284' + test_number

        unmanaged_nfs_mount_props = \
            "export_path='/home/admin/nfs_share_dir/ro_unmanaged' " + \
            "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/5284_test4' "

        unmanaged_nfs_mount_props1 = \
            "export_path='/home/admin/nfs_share_dir/rw_unmanaged' "\
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/5284_test4_b' "

        self.log('info', "1. Create non SFS unmanaged mounts on MS")
        # /test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props)
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # /test2 is read-writeable
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount",
            unmanaged_nfs_mount_props1)
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system2, nfs_mount2)

        self.log('info', "2. Create and run the plan")
        self.create_plan()

        self.log('info', "3. Assert filesystems have been mounted in "
            "/etc/fstab")
        self.check_mount_in_fstab(MOUNTED_FS_NAME3,
                                  MOUNT_PATH_NAME3, self.ms_node)
        self.check_mount_in_fstab(MOUNTED_FS_NAME4,
                                  MOUNT_PATH_NAME4, self.ms_node)

        self.log('info', "4. Check directory permissions")
        self.check_permissions(self.ms_node,
                               file_path='/5284_test4')
        self.check_permissions(self.ms_node,
                               file_path='/5284_test4_b')

        self.log('info', "5. Write to mounted dirs as root")
        filepath = '/5284_test4/my_file.txt'
        file_contents_ls = ['test_write_contents']
        self.assertFalse(self.create_file_on_node(
            self.ms_node, filepath, file_contents_ls, su_root=True))

        filepath = '/5284_test4_b/my_file2.txt'
        file_contents_ls = ['test_write_contents']
        if self.remote_path_exists(self.ms_node, filepath):
            self.remove_item(self.ms_node, filepath, su_root=True)
        self.assertTrue(self.create_file_on_node(
            self.ms_node, filepath, file_contents_ls, su_root=True))
        self.remove_item(self.ms_node, filepath, su_root=True)

        self.log('info', "6. Remove file system and mount")
        self.execute_cli_remove_cmd(self.ms_node, ms_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)

        self.log('info', "7. Create and run plan")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        self.assertTrue(completed_successfully, "Plan was not successful")

        self.log('info', "8. Ensure filesystem and directories have been "
            "removed from the system")
        self.check_mount_not_in_fstab(test_constants.MOUNT_PATH_NAME3,
                                      self.ms_node)
        self.remote_path_exists(self.ms_node, '/5985_test2', expect_file=False)

    # @attr('pre-reg', 'revert', 'story5284', 'story5284_tc05',
    # 'cdb_priority1')
    def obsolete_05_p_create_non_sfs_unmanaged_mounts_nodes(self):
        """
        Merged with
        test_06_p_create_non_sfs_unmanaged_mounts_nodes_in_diff_dirs
        Now covers litpcds_5284_tc08
        #tms_id: litpcds_5284_tc05
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create non sfs unmanaged mounts on the peer nodes
        #tms_description: Test the creation of SFS unmanaged mounts on
        each node
        #tms_test_steps:
            #step: create nfs-service under infrastructure
            #result: nfs-service is created
            #step: create read only unmanaged nfs-mount with
            mount_point='/5284_test5' and inherit on to node1
            #result: nfs-mount is inherited on to the node
            #step: create read only unmanaged nfs-mount with
            mount_point='/5284_test5_b' and inherit on to node2
            #result: nfs-mount is inherited on to the node
            #step: create and run plan
            #result: Plan finishes successfully
            #step: check read only mount exists in /etc/fstab
            #result: read only mount is present
            #step: check read writable mount exists in /etc/fstab
            #result: read writable mount is present
            #step: For each mount check that the ownership is root
            and permissions set to 0755
            #result: The above is correct
            #step: Check that root user cannot write in the read
            only mount
            #result: This is successfully asserted
            #step: Check that root user can write in the writable
            mount
            #result: This is successfully asserted
            #step: Remove file_system and mount
            #result: File system and mount removed
            #step: Ensure filesystem and directories have been removed from
                the system
            #result: The filesystem and directories have been removed
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc06')
    def test_06_p_create_non_sfs_unmanaged_mounts_nodes_in_diff_dirs(self):
        """
        #tms_id: litpcds_5284_tc06
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Create non sfs unmanaged mounts in different
        directories
        #tms_description: Test the creation of SFS unmanaged mounts on
        each node in different directories.
        Covers litpcds_5284_tc05
        #tms_test_steps:
            #step: create nfs-service under infrastructure
            #result: nfs-service is created
            #step: create read only nfs-mount with
            mount_point='/a/b/c/5284_test6'
            #result: nfs-mount created
            #step: Mount the filesystem on the node
            #result: file system is mounted
            #step: create read writable nfs-mount with
            mount_point='/a/b/c/5284_test6_b'
            #result: nfs-mount created
            #step: mount the filesystem to the second mount point
            #result: file system is mounted
            #step: create and run plan
            #result: Plan finishes successfully
            #step: assert file systems have been mounted in /etc/fstab
            #result: file systems have been mounted successfully
            #step: check that the ownership of each mount is root,
            and permissions set to 0755
            #result: The above is correct
            #step: Assert that the read only mount cannot be written to
            by root user
            #result: The above is successfully asserted
            #step: Assert that the read writable mount can be written to
            by root user
            #result: The above is successfully asserted
            #step:  Remove file system and mount
            #result: File system and mount removed
            #step: Create and run plan.
            #result: Plan created
            #step: Ensure filesystem and directories have been removed
                   from the system.
            #result: Filesystem and directories removed successfully.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_num = "_test06"
        grep = "'/home/admin/nfs_share_dir/ro_unmanaged on /5284_test8'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)

        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)

        _, nfs_name = self.__get_non_sfs_path_name()

        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_num
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_num
        nfs_mounts = [nfs_mount, nfs_mount2]
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'

        file_system1_n1 = nodes_url[0] + '/file_systems/nm1_5284' + test_num
        file_system1_n2 = nodes_url[0] + '/file_systems/nm2_5284' + test_num
        file_system2_n1 = nodes_url[1] + '/file_systems/nm1_5284' + test_num
        file_system2_n2 = nodes_url[1] + '/file_systems/nm2_5284' + test_num
        filesystems = [file_system1_n1, file_system1_n2, file_system2_n1,
                       file_system2_n2]
        unmanaged_nfs_mount_props2 = \
            "export_path='/home/admin/nfs_share_dir/ro_unmanaged' " \
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/a/b/c/5284_test6' "

        unmanaged_nfs_mount_props3 = \
            "export_path='/home/admin/nfs_share_dir/rw_unmanaged' " \
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/a/b/5284_test6_b' "

        # /a/b/c/test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", unmanaged_nfs_mount_props3)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # Mount filesystem on the node
        self.execute_cli_inherit_cmd(
            self.ms_node, file_system1_n1, nfs_mount)

        # /a/b/c/test2 is read-writeable)
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount",
            unmanaged_nfs_mount_props2)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system1_n2, nfs_mount2)
        # Mount nfs to mount point 2

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system2_n1, nfs_mount)

        self.execute_cli_inherit_cmd(
            self.ms_node, file_system2_n2, nfs_mount2)

        # Create/run plan, verify success
        self.create_plan()

        for node in self.mn_nodes:
            # Step 4: Assert file system has been mounted in /etc/fstab
            self.check_mount_in_fstab(MOUNTED_FS_NAME4, MOUNT_PATH_NAME4, node)

            # Step 4: Assert file system 2 has been mounted in /etc/fstab
            self.check_mount_in_fstab(MOUNTED_FS_NAME3, MOUNT_PATH_NAME3, node)

            # Step 5. Check permissions on mount
            self.check_permissions(node, file_path='/a/b/c/5284_test6')
            # Step 5. Check permissions on mount
            self.check_permissions(node, file_path='/a/b/5284_test6_b')

            filepath = '/a/b/c/5284_test6/my_file.txt'
            file_contents_ls = ['test_write_contents']
            self.assertFalse(self.create_file_on_node(
                node, filepath, file_contents_ls, su_root=True))

            # Step 6 write to mounted dir as root
            filepath = '/a/b/5284_test6_b/my_file3.txt'
            file_contents_ls = ['test_write_contents']
            if self.remote_path_exists(node, filepath):
                self.remove_item(node, filepath, su_root=True)
            self.assertTrue(self.create_file_on_node(
                node, filepath, file_contents_ls, su_root=True))
            self.remove_item(node, filepath, su_root=True)

        self.log('info', "6. Remove file system and mount")
        for filesystem in filesystems:
            self.execute_cli_remove_cmd(self.ms_node, filesystem)
        for mount in nfs_mounts:
            self.execute_cli_remove_cmd(self.ms_node, mount)

        self.log('info', "7. Create and run plan")
        self.create_plan()

        self.log('info', "8. Ensure filesystem and directories have been "
                         "removed from the system")
        for node in self.mn_nodes:
            self.check_mount_not_in_fstab(grep, node)
            self.remote_path_exists(node, '/a/b/c/5284_test6',
                                    expect_file=False)
            self.remote_path_exists(node, '/a/b/5284_test6_b',
                                    expect_file=False)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc07', 'cdb_priority1')
    def obsolete_07_p_remove_sfs_unmanaged_mount(self):
        """
        Merged with TC03
        #tms_id: litpcds_5284_tc07
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove sfs unmanaged mounts
        #tms_description: Remove a SFS unmanaged mount and ensure that the
        mount is deleted
        #tms_test_steps:
            #step: create sfs-service under infrastructure
            #result: sfs-service is created
            #step: create nfs-mount with mount_point='/5284_test7'
            #result: nfs-mount created
            #step: create and run plan
            #result: Plan finishes successfully
            #step: Remove node 1 file system from the model
            #result: The removal is successful
            #step: Remove the nfs mount
            #result: The removal is successful
            #step: Create and run the plan
            #result: Plan is successful
            #step: Assert mounted file system is no longer in /etc/fstab
            #result: The mounted file system is no longer in /etc/fstab
            #step: Check that /test mount directory is not present
            #result: /test mount directory is not present
            #step: Check that /5284_test7 mount directory is not present
            #result: /5284_test7 is not present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc08', 'cdb_priority1')
    def obsolete_08_p_remove_non_sfs_unmanaged_mount(self):
        """
        Merged with TC06
        #tms_id: litpcds_5284_tc08
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove non sfs unmanaged mounts
        #tms_description: Remove non SFS unmanaged mount and ensure that
        the mount is deleted
        #tms_test_steps:
            #step: create nfs-service under infrastructure
            #result: nfs-service is created
            #step: create nfs-mount with mount_point='/5284_test8'
            #result: nfs-mount created
            #step: create and run plan
            #result: Plan finishes successfully
            #step: Remove mount from the model
            #result: The removal is successful
            #step: Create and run the plan
            #result: Plan is successful
            #step: Assert mounted file system is no longer in /etc/fstab
            #result: The mounted file system is no longer in /etc/fstab
            #step: Check that /test mount directory is not present
            #result: /test mount directory is not present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc09')
    def test_09_p_remove_sfs_and_create_sfs_unmanaged_mount(self):
        """
        #tms_id: litpcds_5284_tc09
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove non sfs unmanaged mounts
        #tms_description: Remove non SFS unmanaged mount and ensure that
        the mount is deleted
        #tms_test_steps:
            #step: Create sfs-service
            #result: sfs-service created
            #step: Create read only nfs-mount with mount_point='/5284_test9'
            #result: nfs-mount is created
            #step: Create and run the plan
            #result: Plan executes successfully
            #step: Remove node file system and nfs-mount from the model
            #result: Items are removed
            #step: Create read/writable nfs-mount
            #result: nfs-mount is created
            #step: Create and run plan
            #result: Plan executes successfully
            #step: Assert file system has been mounted in /etc/fstab
            #result: File system has been mounted in /etc/fstab
            #step: Check that root user can write in /test directory
            #result: Root user can write in /test directory
            #step: Check /test mount directory is present
            #result: /test mount directory is present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test09"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        node_file_system2 = nodes_url[0] + '/file_systems/nm2_5284' \
                            + test_number

        sfs_unmanged_service_props = "name=" + "'" + self.server_name + "'"
        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_point='/5284_test9' "

        nfs_mount_props2 = "export_path='/vx/ossrc1-file_system5' " + \
                           "network_name='mgmt' " + \
                           "provider=" "'" "virtserv1" "' " + \
                           "mount_point='/5284_test9_b' "

        # 1. Create SFS unmanaged mounts on node
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_unmanged_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        # /test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.create_plan()

        # 4. Remove mount from model
        self.execute_cli_remove_cmd(self.ms_node, node_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)

        # Create a nfs-mount read/writable
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount", nfs_mount_props2)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system2, nfs_mount2)

        # 5. Create and run plan
        self.create_plan()

        # 4. Assert file system 2 has been mounted in /etc/fstab
        self.check_mount_in_fstab(MOUNTED_FS_NAME2,
                                  MOUNT_PATH_NAME2, self.mn_nodes[0])

        # 6. user can write in /test directory
        filepath = '/5284_test9_b/my_file2.txt'
        file_contents_ls = ['test_write_contents']
        if self.remote_path_exists(self.mn_nodes[0], filepath):
            self.remove_item(self.mn_nodes[0], filepath, su_root=True)
        self.assertTrue(self.create_file_on_node(
            self.mn_nodes[0], filepath, file_contents_ls, su_root=True))
        self.remove_item(self.mn_nodes[0], filepath, su_root=True)

        # 7. Check /test mount directory is present
        self.remote_path_exists(self.mn_nodes[0], '/5284_test9_b',
                                expect_file=False)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc10')
    def test_10_p_remove_non_sfs_and_create_non_sfs_unmanaged_mount(self):
        """
        #tms_id: litpcds_5284_tc10
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove non sfs and create non sfs unmanaged mounts
        #tms_description: Remove a non-SFS unmanaged mount(ro),
        create a non-sfs unmanaged(rw) in the same location,
        then ensure rw mount point is writable
        #tms_test_steps:
            #step: Create read only nfs-mount with mount_point='/5284_test9'
            #result: nfs-mount is created
            #step: Create and run the plan
            #result: Plan executes successfully
            #step: Remove node file system and nfs-mount from the model
            #result: Items are removed
            #step: Create read/writable nfs-mount
            #result: nfs-mount is created
            #step: Create and run plan
            #result: Plan executes successfully
            #step: Assert file system has been mounted in /etc/fstab
            #result: File system has been mounted in /etc/fstab
            #step: Check that root user can write in /test directory
            #result: Root user can write in /test directory
            #step: Check /test mount directory is present
            #result: /test mount directory is present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test10"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)

        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)

        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        node_file_system2 = nodes_url[0] + '/file_systems/nm2_5284' \
                            + test_number

        _, nfs_name = self.__get_non_sfs_path_name()

        unmanaged_nfs_mount_props = \
            "export_path='/home/admin/nfs_share_dir/ro_unmanaged' " + \
            "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/5284_test10' "

        unmanaged_nfs_mount_props1 = \
            "export_path='/home/admin/nfs_share_dir/rw_unmanaged' "\
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/5284_test10_b' "

        # /test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # Mount filesystem on the node
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.create_plan()

        # 4. Remove mount from model
        self.execute_cli_remove_cmd(self.ms_node, node_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)

        # test2 is read-writeable
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount",
            unmanaged_nfs_mount_props1)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # Mount filesystem on the node
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system2, nfs_mount2)

        # 2/3. Create and run plan
        self.create_plan()

        # 4. Assert file system 2 has been mounted
        self.check_mount_in_fstab(MOUNTED_FS_NAME4,
                                  MOUNT_PATH_NAME4, self.mn_nodes[0])

        # 6. write to mounted dir as root
        filepath = '/5284_test10_b/my_file.txt'
        file_contents_ls = ['test_write_contents']
        if self.remote_path_exists(self.mn_nodes[0], filepath):
            self.remove_item(self.mn_nodes[0], filepath, su_root=True)
        self.assertTrue(self.create_file_on_node(
            self.mn_nodes[0], filepath, file_contents_ls, su_root=True))
        self.remove_item(self.mn_nodes[0], filepath, su_root=True)

        # 7. Check /test mount directory is present
        self.remote_path_exists(self.mn_nodes[0], '/5284_test10_b',
                                expect_file=True)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc11')
    def test_11_p_remove_sfs_and_create_non_sfs_unmanaged_mount(self):
        """
        #tms_id: litpcds_5284_tc11
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove sfs and create non sfs unmanaged mounts
        #tms_description: Remove a SFS unmanaged mount(ro),
        create a non-sfs unmanaged(rw) in the same location,
        then ensure rw mount point is writable.
        #tms_test_steps:
            #step: Create sfs-service
            #result: sfs-service is created
            #step: Create read-writeable nfs-mount with
            mount_point='/5284_test11'
            #result: nfs-mount created
            #step: Create and run the plan
            #result: Plan executes successfully
            #step: Remove node file system and nfs-mount from the model
            #result: Items are removed
            #step: Create read/writable nfs-mount non-sfs unmanaged mount
            #result: nfs-mount is created
            #step: Create and run plan
            #result: Plan executes successfully
            #step: Assert file system has been mounted in /etc/fstab
            #result: File system has been mounted in /etc/fstab
            #step: Assert that root user can not write in /test directory
            #result: Root user can not write in /test directory
            #step: Check /test mount directory is present
            #result: /test mount directory is present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test11"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        node_file_system2 = nodes_url[0] + '/file_systems/nm2_5284' \
                            + test_number

        sfs_unmanged_service_props = "name=" + "'" + self.server_name + "'"
        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_point='/5284_test11' "

        # 1. Create SFS unmanaged mounts on Node (/test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_unmanged_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.create_plan()

        # 4. Remove mount from model
        self.execute_cli_remove_cmd(self.ms_node, node_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)

        # 4. Create non-SFS unmanaged mounts on Node1
        _, nfs_name = self.__get_non_sfs_path_name()

        unmanaged_nfs_mount_props5 = \
            "export_path='/home/admin/nfs_share_dir/ro_unmanaged' " \
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/5284_test11_b' "

        # 5. Create and run plan
        self.create_plan()

        # /a/b/c/test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount",
            unmanaged_nfs_mount_props5)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # Mount filesystem on the node
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system2, nfs_mount2)

        # 5. Create and run plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # Perform the run_plan command
        self.execute_cli_runplan_cmd(self.ms_node)
        completed_successfully = self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE)
        # ensure plan was successful
        self.assertTrue(completed_successfully, "Plan was not successful")

        # 4. Assert file system 2 has been mounted
        self.check_mount_in_fstab(MOUNTED_FS_NAME3,
                                  MOUNT_PATH_NAME3, self.mn_nodes[0])

        # 6. write to mounted dir as root
        filepath = '/5284_test11_b/my_file.txt'
        file_contents_ls = ['test_write_contents']
        self.assertFalse(self.create_file_on_node(
            self.mn_nodes[0], filepath, file_contents_ls, su_root=True))

        # 7. Check /test mount directory is present
        self.remote_path_exists(self.mn_nodes[0], '/5284_test11_b',
                                expect_file=True)

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc12')
    def test_12_p_remove_non_sfs_and_create_sfs_unmanaged_mount(self):
        """
        #tms_id: litpcds_5284_tc12
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Remove non sfs and create sfs unmanaged mounts
        #tms_description: Remove a non-SFS unmanaged mount(ro),
        create a sfs unmanaged(rw) in the same location,
        then ensure rw mount point is writable.
        #tms_test_steps:
            #step: Create nfs-service
            #result: sfs-service is created
            #step: Create read-only nfs-mount with
            mount_point='/a/b/c/5284_test12'
            #result: nfs-mount created
            #step: Create and run the plan
            #result: Plan executes successfully
            #step: Remove node file system and nfs-mount from the model
            #result: Items are removed
            #step: Create and run plan
            #result: Plan executes successfully
            #step: Assert file system has been mounted in /etc/fstab
            #result: File system has been mounted in /etc/fstab
            #step: Assert that root user can not write in /test directory
            #result: Root user can not write in /test directory
            #step: Check /test mount directory is present
            #result: /test mount directory is present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test12"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_number
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        node_file_system2 = nodes_url[0] + '/file_systems/nm2_5284' \
                            + test_number

        _, nfs_name = self.__get_non_sfs_path_name()

        unmanaged_nfs_mount_props4 = \
            "export_path='/home/admin/nfs_share_dir/ro_unmanaged' " \
            + "network_name='mgmt' " + \
            "provider='{0}' ".format(nfs_name) + \
            "mount_options='soft' " + \
            "mount_point='/a/b/c/5284_test12' "

        sfs_unmanged_service_props = "name=" + "'" + self.server_name + "'"
        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_point='/5284_test12' "

        # /a/b/c/test1 mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            unmanaged_nfs_mount_props4)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # Mount filesystem on the node
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)

        # 2/3. Create and run plan
        self.create_plan()

        # 4. Remove mount from model
        self.execute_cli_remove_cmd(self.ms_node, node_file_system)
        self.execute_cli_remove_cmd(self.ms_node, nfs_mount)

        # Create SFS unmanaged mounts on Node /test mount is read only
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_unmanged_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system2, nfs_mount2)

        # 2/3. Create and run plan
        self.create_plan()

        # 6. Assert file system is in fstab
        self.check_mount_in_fstab(MOUNTED_FS_NAME,
                                  MOUNT_PATH_NAME, self.mn_nodes[0])
        # Attempt to write to dir
        filepath = '/t5284_test12/my_file.txt'
        file_contents_ls = ['test_write_contents']
        self.assertFalse(self.create_file_on_node(
            self.mn_nodes[0], filepath, file_contents_ls, su_root=True))
        # 7. Check /test mount directory is present
        self.remote_path_exists(self.mn_nodes[0], '/5284_test12',
                                expect_file=True)

    # @attr('all', 'revert', 'story5284', 'story5284_tc13')
    def obsolete_13_n_sfs_unmanaged_mount_mandatory(self):
        """
        Converted to AT "test_13_n_sfs_unmanaged_mount_mandatory.at" in nasapi
        #tms_id: litpcds_5284_tc13
        #tms_requirements_id: LITPCDS-5284
        #tms_title: sfs unmanaged mount mandatory
        #tms_description: Test that when creating a sfs_unmanaged_mount,
        the required properties, when not entered, throw up the correct error.
        #tms_test_steps:
            #step: Create sfs-service under infrastructure without the 'name'
            property
            #result: Error is output, Expected error:
            #result: 'MissingRequiredPropertyError in property: "name"'
            #step: Create nfs-mount under infrastructure without the required
            properties
            #result: Errors of type 'MissingRequiredPropertyError' are output
            along with each of the following missing properties:
            "mount_point", "provider", "network_name", "export_path"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc14')
    def obsolete_14_n_non_sfs_unmanaged_mount_mandatory(self):
        """
        Converted to AT "test_14_n_non_sfs_unmanaged_mount_mandatory.at" in
        nasapi
        #tms_id: litpcds_5284_tc14
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged mount mandatory
        #tms_description: Test that when creating a non_sfs_unmanaged_mount,
        the required properties, when not entered, throw up the correct error.
        #tms_test_steps:
            #step: Create nfs-service under infrastructure without the 'name'
            property
            #result: Error is output, Expected error:
            #result: 'MissingRequiredPropertyError in property: "name"'
            #step: Create nfs-mount under infrastructure without the required
            properties
            #result: Errors of type 'MissingRequiredPropertyError' are output
            along with each of the following missing properties:
            "mount_point", "provider", "network_name", "export_path"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc15')
    def obsolete_15_n_non_sfs_unmanaged_mount_ipaddress_validation(self):
        """
        Converted to AT
        "test_15_n_non_sfs_unmanaged_mount_ipaddress_validation.at" in nasapi
        #tms_id: litpcds_5284_tc15
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged mount ip address validation
        #tms_description: Test that when creating a non_sfs_unmanaged_mount,
        when creating the nfs_service, the IPv4 and IPv6 are validated.
        #tms_test_steps:
            #step: Create nfs-service under infrastructure with
            ipv4address='10.555.898.7896'
            #result: Validation error is output
            #result: Expected error:
            #result: ValidationError in property: "ipv4address"
            #step: Create nfs-service under infrastructure with
            ipv6address='1200::AB00:1234::2552:7777:1313'
            #result: Validation error is output
            #result: Expected error:
            #result: ValidationError in property: "ipv6address"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc16')
    def obsolete_16_n_sfs_unmanaged_mount_export_path_validation(self):
        """
        Converted to AT
        "test_16_n_sfs_unmanaged_mount_export_path_validation.at" in nasapi
        #tms_id: litpcds_5284_tc16
        #tms_requirements_id: LITPCDS-5284
        #tms_title: sfs unmanaged mount export path validation
        #tms_description: Test that when creating a non_sfs_unmanaged_mount,
        any export_path with an invalid value will throw an error at item
        creation.
        #tms_test_steps:
            #step: Create nfs-mount with invalid export_path value
            export_path='/vx/ossrc1-file_system4?'
            #result: Validation error output
            #result: Output expected:
            'ValidationError in property: "export_path"'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc17')
    def obsolete_17_n_non_sfs_unmanaged_mount_export_path_validation(self):
        """
        Converted to AT
        "test_17_n_non_sfs_unmanaged_mount_export_path_validation.at" in nasapi
        #tms_id: litpcds_5284_tc17
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged mount export point validation
        #tms_description: Test that when creating a non sfs unmanaged_mount,
        when creating the nfs_mount, it should fail.
        #tms_test_steps:
            #step: Create nfs-service under infrastructure with
            name='nfs1'
            #result: nfs-service created
            #step: Create a nfs-mount under infrastructure with
            invalid property export_path='/vx/ossrc1-file_system4?
            #result: Validation error is output
            #result: Expected error:
            'ValidationError in property: "export_path"'
            #step: Create nfs-mount with invalid property
            'export_path='root/abc''
            #result: Validation error output
            #result: Output expected:
            'ValidationError in property: "export_path"'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc18')
    def obsolete_18_n_unmanaged_mount_point_validation(self):
        """
        Converted to test "test_18_n_unmanaged_mount_point_validation.at" in
        nasapi
        #tms_id: litpcds_5284_tc18
        #tms_requirements_id: LITPCDS-5284
        #tms_title: unmanaged mount point validation
        #tms_description: Test that when creating an unmanaged_mount,
        when creating the nfs_mount, it should fail.
        #tms_test_steps:
            #step: Create sfs-service under infrastructure with
            name='sfs'
            #result: sfs-service created
            #step: Create a nfs-mount under infrastructure with invalid
            mount_point=/tmp/home/litp-admin/?nas_plugin_test
            #result: Validation error output
            #result: Output expected:
            'ValidationError in property: "mount_point"'
            #step: Create nfs-mount with mount_point=/nas_plugin_test
            #result: Validation error output
            #result: Output expected:
            'ValidationError in property: "mount_point"'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc19')
    def obsolete_19_n_unmanaged_mount_server_name_duplication(self):
        """
        Converted to "test_19_n_unmanaged_mount_server_name_duplication.at"
        in nas
        #tms_id: litpcds_5284_tc19
        #tms_requirements_id: LITPCDS-5284
        #tms_title: unmanaged mount server name duplication
        #tms_description: Test that checks conflicting name properties for
        an unmanaged mount.
        #tms_test_steps:
            #step: Create sfs-service under infrastructure with
            name='test_20_a'
            #result: sfs-service created
            #step: Create a second sfs-service under infrastructure with
            name='test_20_a'
            #result: sfs-service created
            #step: Try to create plan
            #result: Create plan fails with Validation Error
            #step: Create sfs-service with name='test_20_b'
            #result: sfs-service is created
            #step: Create two sfs-virtual servers with name='test_20_vs1'
            #result: sfs-virtual servers created
            #step: Try to create plan
            #result: Create plan fails with validation error
            #step: Create sfs-virtual-server with name='vsvr1'
            #result: sfs-virtual server created
            #step: Create nfs-service with name='test_20_nfs1'
            #result: nfs-service created
            #step: Try to create plan
            #result: Create plan fails with Validation error
            #step: Create nfs-service with name='test_20_mix'
            #result: nfs-service created
            #step: Create sfs-virtual-server with -o name='test_20_mix'
            #result: sfs-virtual server-created
            #step: Try to create plan, asserting that it won't be positive
            #result: Create plan fails with Validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc20')
    def obsolete_20_n_sfs_unmanaged_mount_mount_point_duplication(self):
        """
        Converted to "test_20_n_sfs_unmanaged_mount_mount_point_duplication.at"
        in nas
        #tms_id: litpcds_5284_tc20
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Sfs unmanaged mount point duplication
        #tms_description: Test that when creating a sfs-unmanaged_mount,
        when creating the nfs_mounts, it should fail when there
        are duplicate mount points.
        #tms_test_steps:
            #step: Create sfs-service under infrastructure with
            name='test_21_a'
            #result: sfs-service created
            #step: create nfs-mount with mount_point=/5284_test20
            #result: nfs-mount created
            #step: Create a second nfs-mount with mount_point=/5284_test20
            #result: nfs-mount created
            #step: Inherit the mounts to node1 filesystem
            #result: mounts are inherited
            #step: Inherit the mounts to the ms filesystem
            #result: mounts are inherited
            #step: Try to create plan, asserting that it won't be
            positive
            #result: Create plan fails with validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc21')
    def obsolete_21_n_non_sfs_unmanaged_mount_mount_point_duplication(self):
        """
        Converted to AT
        "test_21_n_non_sfs_unmanaged_mount_mount_point_duplication.at" in nas
        #tms_id: litpcds_5284_tc21
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged mount point duplication
        #tms_description: Test that when creating an non-sfs-unmanaged_mount,
        when creating the nfs_mounts, it should fail when there
        are duplicate mount points.
        #tms_test_steps:
            #step: Create nfs-service under infrastructure with
            name='nfs1'
            #result: nfs-service created
            #step: create nfs-mount with
            mount_point='/5284_test21'nas_plugin_test
            #result: nfs-mount created
            #step: Create a second nfs-mount with
            mount_point=/5284_test21nas_plugin_test
            #result: nfs-mount created
            #step: Inherit the mounts to node1 filesystem
            #result: mounts are inherited
            #step: Inherit the mounts to the ms filesystem
            #result: mounts are inherited
            #step: Try to create plan, asserting that it won't be
            positive
            #result: Create plan fails with validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc22')
    def obsolete_22_n_sfs_unmanaged_mount_missing_provider(self):
        """
        Converted to AT "test_22_n_sfs_unmanaged_mount_missing_provider.at"
        in nas
        #tms_id: litpcds_5284_tc22
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Sfs unmanaged mount missing provider
        #tms_description: Test the creation of an sfs-unmanaged_mount,
        when creating the nfs_mounts, set the provider as a
        different name than the vip.
        #tms_test_steps:
            #step: Create sfs-service under infrastructure with
            name='test_23_a'
            #result: sfs-service created
            #step: create nfs-mount with
            mount_point=/5284_test22nas_plugin_test
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Try to create plan, asserting that it won't be
            positive
            #result: Create plan fails with validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc23')
    def obsolete_23_n_non_sfs_unmanaged_mount_missing_provider(self):
        """
        Converted to AT "test_23_n_non_sfs_unmanaged_mount_missing_provider.at"
        in nas
        #tms_id: litpcds_5284_tc23
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged mount missing provider
        #tms_description: Test that when creating an non-sfs-unmanaged_mount,
        when creating the nfs_mounts, it should fail when there
        is duplicate mount points.
        #tms_test_steps:
            #step: Create nfs-service under infrastructure with
            name='nfs1'
            #result: nfs-service created
            #step: create nfs-mount with
            mount_point='/5284_test23'nas_plugin_test
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Try to create plan, asserting that it won't be
            positive
            #result: Create plan fails with validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', 'story5284', 'story5284_tc24')
    def obsolete_24_n_unmanaged_mount_provider_duplication(self):
        """
        Converted to AT "test_24_n_unmanaged_mount_provider_duplication.at" in
        nas
        #tms_id: litpcds_5284_tc24
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Unmanaged mount provider duplication
        #tms_description: Test the creation of a sfs-unmanaged_mount,
        and then creating a non-sfs-unmanaged mount,
        and a nfs mount with conflicting names/provider
        #tms_test_steps:
            #step: Create sfs-service under infrastructure with
            name='test_25_a'
            #result: sfs-service created
            #step: Create sfs-virtual server with name='test'
            #result: sfs-virtual server created
            #step: create nfs-service with name='test'
            #result: nfs-service created
            #step: create nfs-mount with
            mount_point=/tmp/home/litp-admin/nas_plugin_test
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Create plan, asserting that it will fail
            #result: Plan fails with validation error.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc25')
    def test_25_n_sfs_unmanaged_server_not_reachable(self):
        """
        #tms_id: litpcds_5284_tc25
        #tms_requirements_id: LITPCDS-5284
        #tms_title: sfs unmanaged server not reachable
        #tms_description: Test that when creating an sfs-unmanaged_mount,
        and giving it a correct IP address but it is not an sfs
        IP. That the plan will fail
        #tms_test_steps:
            #step: Create an nfs-service under infrastructure with
            name='test_26'
            #result: nfs-service created
            #step: Create sfs-virtual server with name='vsvr1'
            #result: sfs-virtual server created
            #step: create nfs-mount with
            mount_point=/5284_test25nas_plugin_test
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Create and run the plan, assert it will fail
            #result: Plan fails
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test25"
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_5284' + test_number
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_5284' + test_number
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_5284' + test_number
        sfs_service_props = "name=" + "'" + "test_26" + "' "
        sfs_virt_server_props = "name='vsvr1' " + \
                                "ipv4address=" + "'" + \
                                "192.168.100.100" + "'"
        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider='vsvr1' " + \
                          "mount_point=/5284_test25" \
                          "nas_plugin_test"

        # 1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service",
            sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story5436.xml")
        self.load_xml(sfsservice_url[0], "xml_story5436.xml")

        # 2. Create the sfs-virtual-server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story5436.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story5436.xml")

        # 3. Create the nfs-mount
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # 4. Inherits
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)

        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # 5. Create the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        # 6. Run the plan
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

    @attr('pre-reg', 'revert', 'story5284', 'story5284_tc26')
    def test_26_n_non_sfs_unmanaged_server_not_reachable(self):
        """
        #tms_id: litpcds_5284_tc26
        #tms_requirements_id: LITPCDS-5284
        #tms_title: Non sfs unmanaged server not reachable
        #tms_description: Test that when creating a non sfs-unmanaged_mount,
        and giving it a correct IP address but it is not an sfs
        IP. That the plan will fail
        #tms_test_steps:
            #step: Create an nfs-service under infrastructure with
            name='vsvr1'
            #result: nfs-service created
            #step: create nfs-mount with mount_point='/5284_test26'
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Create and run the plan, assert it will fail
            #result: Plan fails
            #step: Create an nfs-service under infrastructure with
            name='vsvr2'
            #result: nfs-service created
            #step: create nfs-mount with mount_point='/5284_test26_b'
            #result: nfs-mount created
            #step: Inherit the mount to node1 filesystem
            #result: mount is inherited
            #step: Inherit the mount to the ms filesystem
            #result: mount is inherited
            #step: Create and run the plan, assert that it will fail.
            #result: Plan fails
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        # Test will only pass if the unmanaged FS already exist on the NAS
        # server.
        test_number = "_test26"
        nfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)

        nfs_service = nfsservice_url[0] + '/sp1_5284' + test_number
        nfs_service2 = nfsservice_url[0] + '/sp2_5284' + test_number
        nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                 "storage", True)
        nfs_service_props = "name='vsvr1' " + \
                            "ipv4address=" + "'" + "10.10.10.10"\
                            + "'"
        nfs_service_props2 = "name='vsvr2' " + \
                             "ipv4address=" + "'" + "10.10.10.11"\
                             + "'"
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_5284' + test_number
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount2 = nfsmount_url[0] + '/nfs_mounts/nm2_5284' + test_number
        nfs_mount_props = "export_path='/vx/ossrc1-file_system4' " + \
                          "network_name='mgmt' " + \
                          "provider='vsvr1' " + \
                          "mount_point='/5284_test26'" \
                          "nas_plugin_test"
        nodes_url = self.find(self.ms_node, "/deployments",
                              "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_5284' \
                           + test_number
        node_file_system2 = nodes_url[0] + '/file_systems/nm2_5284' \
                            + test_number
        ms_url = self.find(self.ms_node, "/ms", "file-system-base",
                           rtn_type_children=False, find_refs=True)
        ms_file_system = ms_url[0] + '/nm1_5284' + test_number
        ms_file_system2 = ms_url[0] + '/nm2_5284' + test_number
        nfs_mount_props2 = "export_path='/vx/ossrc1-file_system4' " + \
                           "network_name='mgmt' " + \
                           "provider='vsvr2' " + \
                           "mount_point='/5284_test26_b' "

        # 1. Create NFS-service
        self.execute_cli_create_cmd(
            self.ms_node, nfs_service, "nfs-service",
            nfs_service_props)
        # xml test
        self.export_validate_xml(nfs_service, "xml_story5436.xml")
        self.load_xml(nfsservice_url[0], "xml_story5436.xml")

        # 2. Create the nfs-mounts
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount",
            nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # 3. Inherits
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system, nfs_mount)

        # 4. Create the plan
        self.execute_cli_createplan_cmd(self.ms_node)

        # 5. Run the plan
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

        # 1. Create NFS-service
        self.execute_cli_create_cmd(
            self.ms_node, nfs_service2, "nfs-service",
            nfs_service_props2)
        # xml test
        self.export_validate_xml(nfs_service2, "xml_story5436.xml")
        self.load_xml(nfsservice_url[0], "xml_story5436.xml")

        # 2. Create the nfs-mounts
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount2, "nfs-mount",
            nfs_mount_props2)
        # xml test
        self.export_validate_xml(nfs_mount2, "xml_story5436.xml")
        self.load_xml(nfs_mount_xml, "xml_story5436.xml")

        # 3. Inherits
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system2, nfs_mount2)
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_file_system2, nfs_mount2)

        # 4. Create the plan
        self.execute_cli_createplan_cmd(self.ms_node)

        # 5. Run the plan
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))
