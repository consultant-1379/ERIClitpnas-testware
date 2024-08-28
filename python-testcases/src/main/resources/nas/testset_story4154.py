"""
@copyright: Ericsson Ltd
@since:     September 2014
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-4154
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
from litp_security_utils import SecurityUtils
import test_constants
from xml_utils import XMLUtils


class Story4154(GenericTest):
    """
    LITPCDS-4154:
        The NAS plugin is used to mount or unmount a filesystem in the
         fstab with value provided by the user
    """

    def setUp(self):
        """Run before every test"""
        super(Story4154, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.storage = StorageUtils()
        self.security = SecurityUtils()
        self.xml = XMLUtils()

        self.server_name = self.get_node_att(self.nas_server, "nodetype")
        self.sfs_server_ip = self.get_node_att(self.nas_server, "ipv4")
        self.sfs_server_user = self.get_node_att(self.nas_server, "username")
        self.sfs_server_pw = self.get_node_att(self.nas_server, "password")
        self.ms_ip_address = self.get_node_att(self.ms_node, 'ipv4')
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')
        self.node2_ip_address = self.get_node_att(self.mn_nodes[1], 'ipv4')

        self.export_path = "/vx/story4154-fs1"
        self.pool_name = "litp2"

    def tearDown(self):
        """Run after every test"""
        super(Story4154, self).tearDown()

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
        #this is done in each test to test the item with xml it an
        #already exists error is expected
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
        #expect an output
        self.assertNotEqual([], out)
        #expect no error
        self.assertEqual([], err)
        #expect the return code to equal 0
        self.assertEqual(0, ret_code)
        #expect mount point string
        self.assertTrue(self.is_text_in_list(
            mnt_path, out))

    def litpcrypt(self, key, user_input, password_input):
        """
        Creates and runs a litpcrypt command
        """
        cmd = self.security.get_litpcrypt_set_cmd(service=key,
                                                  user=user_input,
                                                  password=password_input)
        out, err, ret_code = self.run_command(self.ms_node, cmd)
        #expect no output
        self.assertEqual([], out)
        #expect no error
        self.assertEqual([], err)
        #expect the return code to equal 0
        self.assertEqual(0, ret_code)

    @attr('all', 'revert', 'story4154', 'story4154_tc01')
    def obsolete_01_p_ensure_share_created(self):
        """
        Description:
            Test that ensures we can create a share
        Steps:
        1. Create SFS-service,
        2. run litpcrypt
        3. create an sfs-virtual-server
        4. create the export
        5. Create and run the plan
        6. Ensure share was created
        Results:
            Create plan should succeed and the share is created
        """
        export_path = self.export_path + "test1"
        file_system = "story4154-fs1" + "test1"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test1'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test1'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test1" "' " + \
                                "ipv4address=" + "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test1'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            #3. create an sfs-virtual-server
            self.execute_cli_create_cmd(
                self.ms_node, sfs_virt_serv, "sfs-virtual-server",
                sfs_virt_server_props)
            # xml test
            self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
            self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
            #4. create the export
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. Create and run the plan
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            #6. Ensure share was created
            self.assertTrue(self.is_sfs_share_present(self.nas_server,
                                                      export_path))
        finally:
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            self.assertTrue(sfs_del)

    @attr('all', 'revert', 'story4154', 'story4154_tc02')
    def obsolete_02_n_create_duplicate_export(self):
        """
        Description:
            Test that ensures we cannot create an export that already exists
        Steps:
        1. Create SFS-service
        2. run litpcrypt
        3. create an sfs-virtual-server
        4. Create sfs-export
        5. Create another sfs-export
        6. Ensure plan fails to create
        Results:
            Create plan should fail as export already exists
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test2'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.ms_ip_address + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test2'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test2" "' " + \
                                "ipv4address=" + "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test2'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" "/vx/abc-fs1" "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_export_2 = sfs_service + '/exports/ex1_4154_test2_b'
        sfs_export_props_2 = "export_path=" + "'" "/vx/abc-fs1" "' " + \
                             "ipv4allowed_clients=" + "'" + \
                             self.ms_ip_address + "' " + \
                             "export_options=" + "'" "ro,no_root_squash" \
                                                 "' " + \
                             "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user,
                       self.sfs_server_pw)
        #3. create an sfs-virtual-server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #4. Create sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #5. Create another sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export_2, "sfs-export", sfs_export_props_2)
        # xml test
        self.export_validate_xml(sfs_export_2, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #6. Ensure plan fails to create
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'duplicate sfs-export defined')

    @attr('all', 'revert', 'story4154', 'story4154_tc03')
    def obsolete_03_n_create_export_with_invalid_pool(self):
        """
        Description:
            Test that creates an export with an invalid pool_name
        Steps:
        1. Create SFS-service
        2. create an sfs-export with export_path="/vx/abc-fs1" and
        pool_name="doesnotexist'
        3. create and run plan
        4. ensure plan fails and correct error message
        Results:
            Plan should fail
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test3'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.ms_ip_address + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" "doesnotexist" "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test3'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" "/vx/abc-fs1" "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. Create sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #5. Create and run the (unsuccessful) plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

    @attr('all', 'revert', 'story4154', 'story4154_tc04')
    def obsolete_04_p_create_export_and_mount(self):
        """
        Description:
            Test that creates an export and a mount
        Steps:
        1. Create SFS-service
        2. run litpcrypt
        3. Create sfs virtual server
        4. Create sfs-export
        5. Create an nfs-mount on node
        6. inherit mount to node
        7. check plan finished with success
        8. ensure mount is successful on the node
        Results:
            Plan should pass and mount and share should be present
        """
        export_path = self.export_path + "test4"
        file_system = "story4154-fs1" + "test4"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test4'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.sfs_server_ip + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test4'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text4" "' " + \
                                "ipv4address=" + \
                                "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test4'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test4'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_text4" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test4'
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            #3. Create sfs virtual server
            self.execute_cli_create_cmd(
                self.ms_node, sfs_virt_serv, "sfs-virtual-server",
                sfs_virt_server_props)
            # xml test
            self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
            self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. Create an nfs-mount on node
            self.execute_cli_create_cmd(
                self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
            # xml test
            self.export_validate_xml(nfs_mount, "xml_story4154.xml")
            self.load_xml(nfs_mount_xml, "xml_story4154.xml")
            #6. inherit mount to node
            self.execute_cli_inherit_cmd(
                self.ms_node, node_file_system, nfs_mount)
            #7. check plan finished with success
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            #8. check for mount in fstab
            self.check_mount_in_fstab(file_system, export_path,
                                      self.mn_nodes[0])
        finally:
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            self.assertTrue(sfs_del)

    @attr('all', 'revert', 'story4154', 'story4154_tc05')
    def obsolete_05_p_create_export_and_one_mount(self):
        """
        Description:
            Test that creates multiple exports but mounts to one
        Steps:
        1. Create SFS-service
        2. run litpcrypt
        3. Create sfs-export
        and allowed_clients NOT containing 10.10.10.10
        4. Create second sfs-export
        5. Create sfs virtual server
        6. Create an nfs-mount on node
        7. Create Inherit
        8. Check plan finished with success
        9. Ensure share was created
        Results:
            Plan should pass and above items should exist
        """
        export_path = self.export_path + "test5"
        export_path_b = self.export_path + "test5_b"
        file_system = "story4154-fs1" + "test5"
        file_system_b = "story4154-fs1" + "test5_b"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test5'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.sfs_server_ip + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test5'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" \
                                                    + self.node1_ip_address + \
                           "' " + \
                           "export_options=" + "'" "rw" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_export_2 = sfs_service + '/exports/ex1_4154_test5_b'
        sfs_export_props_2 = "export_path=" + "'" + export_path + "_b" + \
                             "' " + \
                             "ipv4allowed_clients=" + "'" \
                                                      + self.node2_ip_address \
                             + "' " + \
                             "export_options=" + "'" \
                                                 "rw" "' " + \
                             "size=" + "'" "10M" "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test5'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text5" "' " + \
                                "ipv4address=" + \
                                "'" + self.sfs_server_ip + "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test5'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_text5" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test5'
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            #3. Create sfs-export
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #4. Create second sfs-export
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export_2, "sfs-export", sfs_export_props_2)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. Create sfs virtual server
            self.execute_cli_create_cmd(
                self.ms_node, sfs_virt_serv, "sfs-virtual-server",
                sfs_virt_server_props)
            # xml test
            self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
            self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
            #6. Create an nfs-mount on node
            self.execute_cli_create_cmd(
                self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
            # xml test
            self.export_validate_xml(nfs_mount, "xml_story4154.xml")
            self.load_xml(nfs_mount_xml, "xml_story4154.xml")
            #7. Create Inherit
            self.execute_cli_inherit_cmd(
                self.ms_node, node_file_system, nfs_mount)
            #8. Check plan finished with success
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            #9. Ensure share was created
            self.assertTrue(self.is_sfs_share_present(self.nas_server,
                                                      export_path))
        finally:
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            if not self.delete_sfs_shares(self.nas_server, export_path_b):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system_b))
            self.assertTrue(sfs_del)

    @attr('all', 'revert', 'story4154', 'story4154_tc06')
    def obsolete_06_n_create_export_with_invalid_allowed_ip(self):
        """
        Description:
            Test that creates an sfs-export with an invalid allowed_client ip
        Steps:
        1. Create SFS-service
        2. create an sfs-export with export_path='/vx/blah' and
        export_options='X'
        and allowed_clients NOT containing 10.10.10.10
        3. create an nfs-mount on node 10.10.10.10 with same "export_path"
        4. create plan
        5. plan should fail with a validation error highlighting that the node
        is not an allowed_client of the export
        Results:
            Plan should fail with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test6'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.ms_ip_address + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test6'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" "/vx/abc-fs1" "' " + \
                           "ipv4allowed_clients=" + "'" \
                                                    "10.10.170.170" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test6'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text6" "' " + \
                                "ipv4address=" + \
                                "'" + self.sfs_server_ip + "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test6'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" "/vx/abc-fs1" "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_text6" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test6'
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. Create sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #3. Create sfs virtual server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #4. Create an nfs-mount on node
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #5.Create Inherit
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        #6. Check plan fails
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr))

    @attr('all', 'revert', 'story4154', 'story4154_tc07')
    def obsolete_07_n_create_conflicting_exports(self):
        """
        Description:
            Test that creates two exports with the same export_path
        Steps:
        1. Create SFS-service
        2. create an sfs-export with export_path='/vx/blah' and
        export_options='X'
        and allowed_clients containing 10.10.10.10
        3. create an sfs-export with export_path='/vx/blah' and
        export_options='Y'
        and allowed_clients containing 10.10.10.10
        4. create an nfs-mount on node 10.10.10.10 with same "export_path"
        5. create plan
        6. plan should fail with a validation error
        Results:
            Plan should fail with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test7'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.ms_ip_address + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test7'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text7" "' " + \
                                "ipv4address=" + \
                                "'" + self.ms_ip_address + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test7'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + "/vx/abc-fs1" + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "export_options=" + "'" "rw" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_export_2 = sfs_service + '/exports/ex1_4154_test7_b'
        sfs_export_props_2 = "export_path=" + "'" + "/vx/abc-fs1" + "' " + \
                             "ipv4allowed_clients=" + "'" + \
                             self.ms_ip_address + "' " + \
                             "export_options=" + "'" "ro" "' " + \
                             "size=" + "'" "20M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test7'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + "/test1" + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_text7" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test7'
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #3. Create sfs virtual server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #4. Create first sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #5. Create second sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export_2, "sfs-export", sfs_export_props_2)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #6. Create an nfs-mount on node
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #7.Create Inherit
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        #8. Ensure create plan fails with correct error
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Create plan failed: Duplicate sfs-export defined '
                        'on sfs-export')

    @attr('all', 'revert', 'story4154', 'story4154_tc08')
    def obsolete_08_n_mount_export_path_not_matching_export(self):
        """
        Description:
            Test that has an incorrect export_path for the nfs_mount than the
            export
        Steps:
        1. Create SFS-service
        2. create an sfs-export with export_path='/vx/blah'
        3. create an nfs-mount on node 10.10.10.10 with different export_path
        4. create plan
        5. check create plan fails with correct error
        Results:
            Create plan should fail with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test8'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + \
                            self.ms_ip_address + "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test8'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" "/vx/abc-fs1" "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test8'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text8" "' " + \
                                "ipv4address=" + \
                                "'" + self.sfs_server_ip + "' "
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test8'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" "/vx/abc-fs2" "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test8" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test8'
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #3. create an sfs-virtual-server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #4. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #5. create an nfs-mount
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #6. Mount on the Node 1
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        #7. create plan
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'nfs-mount "provider" "vsvr1_4154_test8" value')

    @attr('all', 'revert', 'story4154', 'story4154_tc09')
    def obsolete_09_p_create_export_and_mount_with_multiple_ips(self):
        """
        Description:
            Test that creates a managed sfs-export with a list of
            allowed_clients
        Steps:
        1. Create SFS-service
        2. run litpcrypt
        3. create an sfs-export with allowed_clients containing a comma
        separated list of ip addresses
        4. create an nfs-mount with same "export_path"
        5. create and run plan
        6. check plan finished with success
        7. ensure creates the export
        8. ensure mounts on node
        Results:
            Plan should pass and items should be created ok
        """
        export_path = self.export_path + "test9"
        file_system = "story4154-fs1" + "test9"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test9'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test9'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test9" "' " + \
                                "ipv4address=" + "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test9'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test9'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test9" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test9'
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            #3. create an sfs-virtual-server
            self.execute_cli_create_cmd(
                self.ms_node, sfs_virt_serv, "sfs-virtual-server",
                sfs_virt_server_props)
            # xml test
            self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
            self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
            #4. create an sfs-export
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. create an nfs-mount
            self.execute_cli_create_cmd(
                self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
            # xml test
            self.export_validate_xml(nfs_mount, "xml_story4154.xml")
            self.load_xml(nfs_mount_xml, "xml_story4154.xml")
            #6. Mount on the Node 1
            self.execute_cli_inherit_cmd(
                self.ms_node, node_file_system, nfs_mount)
            #7. create and run plan
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            #8. Ensure mounts
            self.check_mount_in_fstab(file_system, export_path,
                                      self.mn_nodes[0])
        finally:
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            self.assertTrue(sfs_del)

    @attr('all', 'revert', 'story4154', 'story4154_tc10')
    def obsolete_10_n_export_with_invalid_ipv4allowed_clients_range(self):
        """
        Description:
            Test that creates an sfs-export with ipv4allowed_clients that
            contains a range
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv4allowed_clients containing a range
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test10'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test10'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.*" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4allowed_clients"', stderr),
                        "Invalid value '10.46.71.*'.")

    @attr('all', 'revert', 'story4154', 'story4154_tc11')
    def obsolete_11_n_export_with_invalid_allowed_clients_not_comma(self):
        """
        Description:
            Test that creates an sfs-export with ipv4allowed_clients that
            doesn't contain commas
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv4allowed_clients containing a list
        of ipv4 addresses separated
        by a delimiter other than a comma
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test11'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test11'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.25.47." \
                                                    "24.87.54!74.87." \
                                                    "41.41" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "1G" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4allowed_clients"', stderr),
                        "Invalid value '10.46.71.25.47.24.87.54!74.87.41.41'")

    @attr('all', 'revert', 'story4154', 'story4154_tc12')
    def obsolete_12_n_export_with_invalid_allowed_clients_not_ipv4s(self):
        """
        Description:
            Test that creates an sfs-export with ipv4allowed_clients that
            doesn't contain valid ip4s
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv4allowed_clients containing a list
        of comma separated strings (not IPv4's)
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test12'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test12'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv4allowed_clients=" + "'" "ipone,iptwo," \
                                                    "ipthree" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4allowed_clients"', stderr),
                        "Invalid value 'ipone,iptwo,ipthree'")

    @attr('all', 'revert', 'story4154', 'story4154_tc13')
    def obsolete_13_n_export_with_invalid_ipv6allowed_clients_range(self):
        """
        Description:
            Test that creates an sfs-export with ipv6allowed_clients
            that contains a range
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv6allowed_clients containing a range
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test13'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test13'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv6allowed_clients=" + "'" "1200::AB00:1234:" \
                                                    ":2552:7777:*" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv6allowed_clients"', stderr),
                        "Invalid value '1200::AB00:1234::2552:7777:*'")

    @attr('all', 'revert', 'story4154', 'story4154_tc14')
    def obsolete_14_n_export_invalid_ipv6allowed_clients_not_comma(self):
        """
        Description:
            Test that creates an sfs-export with ipv6allowed_clients that
            doesn't contain commas
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv6allowed_clients containing a list of
        ipv6 addresses separated
        by a delimiter other than a comma
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test14'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test14'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv6allowed_clients=" + "'" "aa:bb:00::?aa" \
                                                    ":bb:00::" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv6allowed_clients"', stderr),
                        "Invalid value 'aa:bb:00::?aa:bb:00::'")

    @attr('all', 'revert', 'story4154', 'story4154_tc15')
    def obsolete_15_n_export_with_invalid_allowed_clients_not_ipv6s(self):
        """
        Description:
            Test that creates an sfs-export with ipv6allowed_clients that
            doesn't contain valid ip6s
        Steps:
        1. Create SFS-service
        2. create an sfs-export with ipv6allowed_clients containing a lists
        of comma separated strings (not IPv4's)
        3. create item should fail with correct error message
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test15'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test15'
        sfs_export_props = "export_path='/vx/story4154-fs1' " + \
                           "ipv6allowed_clients=" + "'" "ipone,iptwo," \
                                                    "ipthree" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with ipv4allowed_clients containing a range
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv6allowed_clients"', stderr),
                        '"ipone" is invalid, only accepts a list of valid '
                        'IPv6 addresses separated by single commas')

    @attr('all', 'revert', 'story4154', 'story4154_tc16')
    def obsolete_16_n_create_service_with_invalid_key(self):
        """
        Description:
            Test that creates an sfs-service with an invalid key
        Steps:
        1. create an sfs-service with key not in keystore but a valid
        user="support"
        2. create an sfs-virtual-server
        3. create an sfs-export
        4. create an nfs-mount
        5. Ensure create plan fails with correct error
        Results:
            Create plan should fail with the correct error
        """
        export_path = self.export_path + "test16"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test16'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-blah" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test16'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test16" "' " + \
                                "ipv4address=" + "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test16'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test16'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test16" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create an sfs-virtual-server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create an nfs-mount
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #5. Ensure create plan fails with correct error
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('Credentials not found    '
                                             'Create plan failed:', stderr),
                        'Not able to find credentials for plugin nas_plugin, '
                        'for service "key-for-blah", user "support"')

    @attr('all', 'revert', 'story4154', 'story4154_tc17')
    def obsolete_17_n_create_service_with_invalid_user(self):
        """
        Description:
            Test that creates an sfs-service with an invalid user
        Steps:
        1. create an sfs-service with user not in keystore but a valid key
        2. validation should fail with correct error
        Results:
            Create Item should fail with correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test17'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "user_name=" + "'" "master" "' " + \
                            "password_key=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        #1. Create SFS-service
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"user_name"', stderr),
                        '"master" is not an allowed value')

    @attr('all', 'revert', 'story4154', 'story4154_tc18')
    def obsolete_18_n_create_export_with_size_larger_than_pool(self):
        """
        Description:
            Test that creates an sfs-export with a larger than available size
        Steps:
        1. create an sfs-service
        2. run litpcrypt
        3. create sfs-virtual-server
        4. create sfs-export with a large "size"
        5. create nfs-mount
        6. create and run plan
        7. plan should fail with correct error
        Results:
            PLan should fail with error
        """
        export_path = self.export_path + "test18"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test18'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test18'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test18" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test18'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw" "' " + \
                           "size=" + "'" "5000G" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test18'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test18" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test18'
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        #xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #3. create an sfs-virtual-server
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        #xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #4. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        #xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #5. create an nfs-mount
        self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props)
        #xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #6. Create Inherit
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        #7. create and run plan (failing)
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

    @attr('all', 'revert', 'story4154', 'story4154_tc19')
    def obsolete_19_n_export_with_invalid_sysid(self):
        """
        Description:
            Test that creates an sfs-export with an invalid sysid
        Steps:
        1. create an sfs-service
        2. create an sfs-export with export_path where the sysid has an
        invalid character (!? etc.)
        3. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test19'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test19'
        sfs_export_props = "export_path='/vx/@!-fs1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.150" "' " + \
                           "virtual_server=" + "'" "vsvr1_4154_test19" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path where the sysid has an
        # invalid character
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_path"', stderr),
                        "Invalid value '/vx/@!-fs1'")

    @attr('all', 'revert', 'story4154', 'story4154_tc20')
    def obsolete_20_n_export_with_invalid_file_system(self):
        """
        Description:
            Test that creates an sfs-export with an invalid file_system
        Steps:
        1. create an sfs-service
        2. create an sfs-export with export_path where the file_system
        has an invalid character (!? etc.)
        3. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test20'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test20'
        sfs_export_props = "export_path='/vx/story4154-@!1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.153" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path where the file_system
        # has an invalid character
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_path"', stderr),
                        "Invalid value '/vx/story4154-@!1'")

    @attr('all', 'revert', 'story4154', 'story4154_tc21')
    def obsolete_21_n_export_with_no_hyphen(self):
        """
        Description:
            Test that creates an sfs-export without a hyphen
        Steps:
        1. create an sfs-service
        2. create an sfs-export with export_path with no hyphen
        3. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test21'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test21'
        sfs_export_props = "export_path='/vx/story4154fs1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.154" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path with no hyphen
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_path"', stderr),
                        "The sysid cannot be defined from the export_path")

    @attr('all', 'revert', 'story4154', 'story4154_tc22')
    def obsolete_22_n_export_over_max_length(self):
        """
        Description:
            Test that creates an sfs-export that's too long
        Steps:
        1. create an sfs-service
        2. create an sfs-export with export_path of greater length than 29
        characters
        3. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test22'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test22'
        sfs_export_props = "export_path='/vx/story4154-fs1xxxxxxxxxxxxxx" \
                           "xxxxxxxxxxxxxx' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.155" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path of greater length than
        # 29 characters
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_path"', stderr),
                        "export_path should not be greater than 29 "
                        "characters in length")

    @attr('all', 'revert', 'story4154', 'story4154_tc23')
    def obsolete_23_n_export_with_incorrect_prefix(self):
        """
        Description:
            Test that creates an sfs-export with an incorrect prefix
        Steps:
        1. create an sfs-service
        2. create an sfs-export with export_path with an incorrect prefix
        3. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test23'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test23'
        sfs_export_props = "export_path='/vg/story4154-fs1' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.156" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path with an incorrect prefix
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_path"', stderr),
                        'sfs-export should begin with "/vx/"')

    @attr('all', 'revert', 'story4154', 'story4154_tc24')
    def obsolete_24_n_login_details_must_exist(self):
        """
        Description:
            Test that creates an sfs-service without the login details
        Steps:
        1. create an sfs-service without specifying the login details
        2. ensure error is correct
        Results:
            Should fail to item creation
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test24'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "pool_name=" + "'" + self.pool_name + "'"
        #1. create an sfs-service without specifying the login details
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'If the sfs-service is managed, the following '
                        'attribute(s) should be added: "user_name", '
                        '"password_key".')

    @attr('all', 'revert', 'story4154', 'story4154_tc25')
    def obsolete_25_n_pool_name_required(self):
        """
        Description:
            Test that creates an sfs-service without the pool_name property
        Steps:
        1. create an sfs-service without specifying a pool_name
        2. ensure error is correct
        Results:
            Should fail to create item
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test25'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + "'"
        #1. create an sfs-service without specifying a pool_name
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'If the sfs-service is managed, the following '
                        'attribute(s) should be added: "pool_name".')

    @attr('all', 'revert', 'story4154', 'story4154_tc26')
    def obsolete_26_n_invalid_pool_name(self):
        """
        Description:
            Test that creates an sfs-service with an invalid value for
            "pool_name"
        Steps:
        1. create an sfs-service with pool_name = "!?"
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test26'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" "!?" "'"
        #1. create an sfs-service with pool_name = "!?"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"pool_name"', stderr),
                        "Invalid value '!?'")

    @attr('all', 'revert', 'story4154', 'story4154_tc27')
    def obsolete_27_n_export_path_required(self):
        """
        Description:
            Test that creates an sfs-export without the export_path property
        Steps:
        1. create an sfs-export without the export_path property
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test27'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test27'
        sfs_export_props = "ipv4allowed_clients=" + "'" "10.46.71.156" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export without the export_path property
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('MissingRequiredPropertyError in'
                                             ' property: "export_path"',
                                             stderr), 'ItemType "sfs-export" '
                                                      'is required to have a '
                                                      '"property" with name '
                                                      '"export_path"')

    @attr('all', 'revert', 'story4154', 'story4154_tc28')
    def obsolete_28_n_export_requires_allowed_clients(self):
        """
        Description:
            Test that creates an sfs-export without the export_path property
        Steps:
        1. create an sfs-export without ipv4 or ipv6 allowed_clients
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test28"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test28'
        sfs_service_props = "name=" + "'" + self.server_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test28'
        sfs_export_props = "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "export_path=" + "'" + export_path + "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export with export_path where the sysid has
        # an invalid character
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4allowed_clients"', stderr),
                        'Either "ipv4allowed_clients" or '
                        '"ipv6allowed_clients" must be defined.')

    @attr('all', 'revert', 'story4154', 'story4154_tc29')
    def obsolete_29_n_export_requires_export_options(self):
        """
        Description:
            Test that creates an sfs-export without a export_options property
        Steps:
        1. create an sfs-export without export_options
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test29"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test29'
        sfs_service_props = "name=" + "'" + self.server_name + "' " \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test29'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(self.ms_node, sfs_service, "sfs-service",
                                    sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #1. create an sfs-export without export_options
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('MissingRequiredPropertyError in'
                                             ' property: "export_options"',
                                             stderr),
                        'ItemType "sfs-export" is required to have a '
                        '"property" with name "export_options"')

    @attr('all', 'revert', 'story4154', 'story4154_tc30')
    def obsolete_30_n_export_valid_export_options(self):
        """
        Description:
            Test that creates an sfs-export with invalid export_options
        Steps:
        1. create an sfs-export with export_options separated by a
        delimiter other than a comma
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test30"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test30'
        sfs_service_props = "name=" + "'" + self.server_name + "' " \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test30'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw/no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #Export_options with delimiter other than comma
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_options"', stderr),
                        "rw/no_root_squash is an invalid export_option")

    @attr('all', 'revert', 'story4154', 'story4154_tc31')
    def obsolete_31_n_export_conflicting_export_options(self):
        """
        Description:
            Test that creates an sfs-export with export_options that conflict
        Steps:
        1. create an sfs-export with export_options containing
        conflicting options (soft + hard)
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test31"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test31'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test31'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,ro,no_root_squash" \
                                               "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. create an sfs-export
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"export_options"', stderr),
                        "Conflicting export options inputted rw,ro")

    @attr('all', 'revert', 'story4154', 'story4154_tc32')
    def obsolete_32_n_export_requires_size(self):
        """
        Description:
            Test that creates an sfs-export without the required "size"
            property
        Steps:
        1. create an sfs-export without the "size" property
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test32"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test32'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test32'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' "
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #3. create an sfs-export
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('MissingRequiredPropertyError '
                                             'in property: "size"', stderr),
                        'ItemType "sfs-export" is required to have a " \
                                             ""property" with name "size"')

    @attr('all', 'revert', 'story4154', 'story4154_tc33')
    def obsolete_33_n_export_valid_size_start(self):
        """
        Description:
            Test that creates an sfs-export with an invalid value for "size"
        Steps:
        1. create an sfs-export with size property that begins with 0
        2. ensure item creation failure with correct message
        3. create an sfs-export with size property that begins with a letter
        4. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test33"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test33'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test33'
        sfs_export_props1 = "export_path=" + "'" + export_path + "' " + \
                            "ipv4allowed_clients=" + "'" "10.46.71.10" "' " +\
                            "export_options=" + "'" "rw,no_root_squash" \
                                                "' " + \
                            "size=" + "'" "0M" "'"
        sfs_export_props2 = "export_path=" + "'" + export_path + "' " + \
                            "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                            "export_options=" + "'" "rw,no_root_squash" \
                                                "' " + \
                            "size=" + "'" "PM" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #3. create an sfs-export
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props1,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"size"', stderr),
                        "Invalid value '0M'")
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props2,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"size"', stderr),
                        "Invalid value 'PM'")

    @attr('all', 'revert', 'story4154', 'story4154_tc34')
    def obsolete_34_n_export_valid_size_end(self):
        """
        Description:
            Test that creates an sfs-export with an invalid value for "size"
        Steps:
        1. create an sfs-export with size property that ends with something
        other than a "M", "G" or "T".
        2. ensure item creation failure with correct message
        Results:
            The item should fail to create with the correct error
        """
        export_path = self.export_path + "test34"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test34'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + self.sfs_server_pw + \
                            "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test34'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "1K" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #3. create an sfs-export
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"size"', stderr),
                        "Invalid value '1K'")

    @attr('all', 'revert', 'story4154', 'story4154_tc35')
    def obsolete_35_n_invalid_mount_provider(self):
        """
        Description:
            Test that creates an nfs-mount with a invalid provider
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with a provider that doesn't match a
        "name" of the vip
        5. create plan
        6. ensure error is correct
        Results:
            The plan should fail
        """
        export_path = self.export_path + "test35"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test35'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test35'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test35" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test35'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/nm1_4154_test35'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'""vsvr1_4154_test35_incorrect""' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node_file_system = nodes_url[0] + '/file_systems/nm1_4154_test35'
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with a export_path that doesn't match a
        # "export_path" of the sfs-export
        self.execute_cli_create_cmd(self.ms_node, nfs_mount, "nfs-mount",
                                    nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #7.Create Inherit
        self.execute_cli_inherit_cmd(
            self.ms_node, node_file_system, nfs_mount)
        #8. Ensure create plan fails with correct error
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'nfs-mount "provider" "vsvr1_4154_test35_incorrect" '
                        'value')

    @attr('all', 'revert', 'story4154', 'story4154_tc36')
    def obsolete_36_n_invalid_mount_export_path(self):
        """
        Description:
            Test that creates an nfs-mount with a invalid export_path
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with a export_path that doesn't match a
        "export_path" of the sfs-export
        5. create plan
        6. run plan
        7. ensure error
        Results:
            The plan should fail
        """
        export_path = self.export_path + "test36"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test36'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test36'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test36" "' " + \
                                "ipv4address=" + "''" + self.sfs_server_ip + \
                                "'' "
        sfs_export = sfs_service + '/exports/ex1_4154_test36'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test36'
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_props = "export_path=" "'" "/vx/edcba-fs2" "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test36" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with a export_path that doesn't match a
        # "export_path" of the sfs-export
        self.execute_cli_create_cmd(self.ms_node, nfs_mount, "nfs-mount",
                                    nfs_mount_props)
        # xml test
        self.export_validate_xml(nfs_mount, "xml_story4154.xml")
        self.load_xml(nfs_mount_xml, "xml_story4154.xml")
        #5. Create the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

    @attr('all', 'revert', 'story4154', 'story4154_tc37')
    def obsolete_37_n_invalid_mount_mount_options(self):
        """
        Description:
            Test that creates an nfs-mount with invalid mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options separated by a delimiter
        other than a comma
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test37"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test37'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test37'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test37" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test37'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test37'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test37" "' " + \
                          "mount_options=" "'" "soft.timeo=1000" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options separated by a delimiter
        # other than a comma
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "soft.timeo is not a valid mount_option.")

    @attr('all', 'revert', 'story4154', 'story4154_tc38')
    def obsolete_38_n_conflicting_mount_mount_options(self):
        """
        Description:
            Test that creates an nfs-mount with conflicting mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing both "soft"
        and "hard"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test38"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test38'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test38'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test38" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test38'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test38'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test38" "' " + \
                          "mount_options=" "'" "soft,hard" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing both "soft"
        # and "hard"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "conflicting mount options.")

    @attr('all', 'revert', 'story4154', 'story4154_tc39')
    def obsolete_39_n_invalid_mount_options_value(self):
        """
        Description:
            Test that creates an nfs-mount with a invalid mount_option
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing acregmin="invalid"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test39"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test39'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test39'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test39" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test39'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test39'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test39" "' " + \
                          "mount_options=" "'" "acregmin='invalid'" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing acregmin="invalid"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "acregmin mount_option requires a numeric value.")

    @attr('all', 'revert', 'story4154', 'story4154_tc40')
    def obsolete_40_n_invalid_sec_mount_option(self):
        """
        Description:
            Test that creates an nfs-mount and has an invalid "sec" value in
            mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing sec="invalid"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test40"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test40'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test40'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test40" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test40'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test40'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test40" "' " + \
                          "mount_options=" "'" "sec='invalid'" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing sec="invalid"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "invalid is an invalid sec value.")

    @attr('all', 'revert', 'story4154', 'story4154_tc41')
    def obsolete_41_n_invalid_proto_mount_option(self):
        """
        Description:
            Test that creates an nfs-mount and has an invalid "proto" value in
             mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing proto="invalid"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test41"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test41'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test41'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test41" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test41'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test41'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test41" "' " + \
                          "mount_options=" "'" "proto='invalid'" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing proto="invalid"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "invalid is an invalid proto value.")

    @attr('all', 'revert', 'story4154', 'story4154_tc42')
    def obsolete_42_n_invalid_lookupcache_mount_option(self):
        """
        Description:
            Test that creates an nfs-mount and has an invalid "lookupcache"
            property in mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing
        lookupcache="invalid"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test42"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test42'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test42'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test42" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test42'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test42'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test42" "' " + \
                          "mount_options=" "'" "soft,lookupcache='invalid'" \
                          "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing
        # lookupcache="invalid"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "invalid is an invalid lookupcache option.")

    @attr('all', 'revert', 'story4154', 'story4154_tc43')
    def obsolete_43_n_invalid_clientaddr_mount_option(self):
        """
        Description:
            Test that creates an nfs-mount and has an invalid "clientaddr"
            value in mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing
        clientaddr="invalid"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test43"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test43'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test43'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test43" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test43'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test43'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test43" "' " + \
                          "mount_options=" "'" "soft,clientaddr='invalid'" \
                          "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing
        # clientaddr="invalid"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "clientaddr clientaddr option has invalid ip.")

    @attr('all', 'revert', 'story4154', 'story4154_tc44')
    def obsolete_44_n_invalid_timeo_mount_option(self):
        """
        Description:
            Test that creates an nfs-mount and has conflicting properties with
            the "timeo" property in mount_options
        Steps:
        1. create sfs-service
        2. create a vip
        3. create an sfs-export
        4. create a nfs-mount with mount_options containing "timeo" and not
        containing "soft"
        5. ensure item creation fails with correct error message
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test44"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test44'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "''" + self.ms_ip_address + \
                            "'' " +\
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" "key-for-sfs" "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test44'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test44" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test44'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        nfs_mount = nfsmount_url[0] + '/nfs_mounts/ms1_4154_test44'
        nfs_mount_props = "export_path=" "'" + export_path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "vsvr1_4154_test44" "' " + \
                          "mount_options=" "'" "timeo=1000" "' " + \
                          "mount_point=" + "'" "/test1" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        #2. create a vip
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        #3. create an sfs-export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        #4. create a nfs-mount with mount_options containing "timeo" and
        # not containing "soft"
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, nfs_mount, "nfs-mount", nfs_mount_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"mount_options"', stderr),
                        "unable to use timeo without soft option mount_option")

    @attr('all', 'revert', 'story4154', 'story4154_tc45')
    def obsolete_45_n_create_sfs_service_with_ipv4_and_ipv6(self):
        """
        Description:
            Test that creates a service with both management_ip's
        Steps:
        1. create an sfs-service with both a management_ipv4 and
        management_ipv6
        2. create plan
        3. ensure error is correct
        Results:
            Item creation should fail
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test45'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "management_ipv6=" + "'" "aa:bb:00::" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        #1. Create SFS-service
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Only "management_ipv4" or "management_ipv6" '
                        'may be defined for an sfs-service but not both')

    @attr('all', 'revert', 'story4154', 'story4154_tc46')
    def obsolete_46_n_create_vip_with_ipv4_and_ipv6(self):
        """
        Description:
            Test that creates a vip with both management_ip's
        Steps:
        1. create an sfs-service with a management_ipv4
        2. create a vip with ipv4address and ipv6address
        3. ensure error in item creation
        4. ensure error is correct
        Results:
            Item creation should fail
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test46'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test46'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text48" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' " + \
                                "ipv6address=" + "'" "aa:bb:00::" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4address"', stderr),
                        '"ipv4address" or "ipv6address" can '
                        'be defined but not both.')

    @attr('all', 'revert', 'story4154', 'story4154_tc47')
    def obsolete_47_n_create_export_with_ipv4_and_ipv6(self):
        """
        Description:
            Test that creates a export with both ipallowed_clients
        Steps:
        1. create an sfs-service with a management_ipv4
        2. create a vip with ipv4address
        3. create an export with ipv4allowed_clients and ipv6allowed_clients
        4. ensure error in item creation
        5. ensure error is correct
        Results:
            Item creation should fail
        """
        export_path = self.export_path + "test47"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test47'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test47'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text49" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test47'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "ipv6allowed_clients=" + "'" "aa:bb:00::" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props,
            expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError in property: '
                                             '"ipv4allowed_clients"', stderr),
                        '"ipv4allowed_clients" or "ipv6allowed_clients" '
                        'can be defined but not both.')

    @attr('all', 'revert', 'story4154', 'story4154_tc48')
    def obsolete_48_n_create_export_with_ipv6_under_ipv4(self):
        """
        Description:
            Test that creates an 1pv6 export with a ipv4 service and vip
        Steps:
        1. create an sfs-service with a management_ipv4
        2. create a vip with ipv4address
        3. create an export with ipv6allowed_clients
        4. create plan
        5. ensure error is present and correct
        Results:
            Create plan should fail
        """
        export_path = self.export_path + "test48"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test48'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test48'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text50" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test48'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv6allowed_clients=" + "'" "aa:bb:00::" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        '"sfs-export" should be defined with the same '
                        'internet protocol as the sfs-service')

    @attr('all', 'revert', 'story4154', 'story4154_tc49')
    def obsolete_49_n_create_vip_with_ipv6_under_ipv4(self):
        """
        Description:
            Test that creates an ipv6 vip with a ipv4 service and export
        Steps:
        1. create an sfs-service with a management_ipv4
        2. create a vip with ipv6address
        3. create an export with ipv4allowed_clients
        4. create plan
        5. ensure error is present and correct
        Results:
            Create plan should fail
        """
        export_path = self.export_path + "test49"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test49'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test49'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text51" "' " + \
                                "ipv6address=" + "'" "aa:bb:00::" "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test49'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
                # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        '"sfs-virtual-server" should be defined with the '
                        'same internet protocol as the sfs-service')

    @attr('all', 'revert', 'story4154', 'story4154_tc50')
    def obsolete_50_n_create_export_with_ipv4_under_ipv6(self):
        """
        Description:
            Test that creates an ipv4 export with a ipv6 service and vip
        Steps:
        1. create an sfs-service with a management_ipv6
        2. create a vip with ipv6address
        3. create an export with ipv4allowed_clients
        4. create plan
        5. ensure error is present and correct
        Results:
            Create plan should fail
        """
        export_path = self.export_path + "test50"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test50'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv6=" + "'" "aa:bb:00::" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test50'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_text50" "' " + \
                                "ipv6address=" + "'" "aa:bb:00::" "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test50'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" "10.46.71.10" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
                # xml test
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        '"sfs-export" should be defined with the same '
                        'internet protocol as the sfs-service')

    @attr('all', 'revert', 'story4154', 'story4154_tc51')
    def obsolete_51_n_create_vip_with_ipv4_under_ipv6(self):
        """
        Description:
            Test that creates an ipv4 vip with a ipv6 service and export
        Steps:
        1. create an sfs-service with a management_ipv6
        2. create a vip with ipv4address
        3. create an export with ipv6allowed_clients
        4. create plan
        5. ensure error is present and correct
        Results:
            Create plan should fail
        """
        export_path = self.export_path + "test51"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test51'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv6=" + "'" "aa:bb:00::" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test51'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test51" "' " + \
                                "ipv4address=" + "'" + \
                                self.sfs_server_ip + "' "
        sfs_export = sfs_service + '/exports/ex1_4154_test51'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv6allowed_clients=" + "'" "aa:bb:00::" "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_virt_serv, "sfs-virtual-server",
            sfs_virt_server_props)
        self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
        self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        '"sfs-virtual-server" should be defined with the '
                        'same internet protocol as the sfs-service')

    @attr('all', 'revert', 'story4154', 'story4154_tc52')
    def obsolete_52_n_two_sfs_service_with_duplicate_management_ipv4s(self):
        """
        Description:
            Test that creates two sfs services with duplicate management IPv4
            addresses
        Steps:
        1. create an sfs-service with a management_ipv4=10.10.10.10
        2. create a second sfs-service with a management_ipv4=10.10.10.10
        3. create plan
        4. ensure error is present and correct
        Results:
            Create plan should fail
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test52'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" "10.10.10.10" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_service2 = sfsservice_url[0] + '/sp1_4154_test52_b'
        sfs_service_props2 = "name=" + "'" + self.server_name + "2" + "' " + \
                             "management_ipv4=" + "'" "10.10.10.10" "' " + \
                             "user_name=" + "'" + self.sfs_server_user + \
                             "' " + \
                             "password_key=" + "'" + "key-for-sfs" + "' " \
                             + \
                             "pool_name=" + "'" + self.pool_name + "'"
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service2, "sfs-service", sfs_service_props2)
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Duplicate "management_ipv4" address '
                        '"10.10.10.10" defined on sfs service')

    @attr('all', 'revert', 'story4154', 'story4154_tc53')
    def obsolete_53_n_two_sfs_service_with_duplicate_management_ipv6s(self):
        """
        Description:
            Test that creates two sfs services with duplicate management IPv6
            addresses
        Steps:
        1. create an sfs-service with a
        management_ipv6="FE80:0000:0000:0000:0202:B3FF:FE1E:8329"
        2. create a second sfs-service with a
        management_ipv6="FE80:0000:0000:0000:0202:B3FF:FE1E:8329"
        3. create plan
        4. ensure error is present and correct
        Results:
            Create plan should fail
        """
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test53'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv6=" + "'" "aa:bb:00::" "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_service2 = sfsservice_url[0] + '/sp1_4154_test53_b'
        sfs_service_props2 = "name=" + "'" + self.server_name + "2" + "' " + \
                             "management_ipv6=" + "'" "aa:bb:00::" "' " + \
                             "user_name=" + "'" + self.sfs_server_user + \
                             "' " + \
                             "password_key=" + "'" + "key-for-sfs" + "' " \
                             + \
                             "pool_name=" + "'" + self.pool_name + "'"
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service2, "sfs-service", sfs_service_props2)
        # run litpcrypt
        self.litpcrypt("key-for-sfs", self.sfs_server_user, self.sfs_server_pw)
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Duplicate "management_ipv6" address '
                        '"aa:bb:00::" defined on sfs service')

    @attr('all', 'revert', 'story4154', 'story4154_tc54')
    def obsolete_54_n_create_an_sfs_service_with_user_does_not_exist(self):
        """
        Description:
            Test that creates a SFS service with an incorrect
            username property
        Steps:
        1. create an sfs-service whereby user does not exist on the SFS
        2. create an export
        3. create and run plan
        4. check logs for error
        Results:
            Create plan should fail
        """
        export_path = self.export_path + "test54"
        key = "key-for-jimmy"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test54'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" "jimmy" "' " + \
                            "password_key=" + "'" + key + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test54'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        #1. Create SFS-service
        self.execute_cli_create_cmd(
            self.ms_node, sfs_service, "sfs-service", sfs_service_props)
        # xml test
        self.export_validate_xml(sfs_service, "xml_story4154.xml")
        self.load_xml(sfsservice_url[0], "xml_story4154.xml")
        #2. run litpcrypt
        self.litpcrypt(key, "jimmy", "jimmy")
        #3. create the export
        self.execute_cli_create_cmd(
            self.ms_node, sfs_export, "sfs-export", sfs_export_props)
        # xml test
        self.export_validate_xml(sfs_export, "xml_story4154.xml")
        self.load_xml(sfs_export_xml, "xml_story4154.xml")
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.PLAN_FAILED))

    @attr('all', 'revert', 'story4154', 'story4154_tc55')
    def obsolete_55_p_two_exports_with_different_allowed_clients(self):
        """
        Description:
            Test that creates 2 exports with different allowed clients
        Steps:
        1. create an sfs-service
        2. create an sfs-export with allowed_clients=10.10.10.10 and
        export_path=/vx/abcds-test
        3. create and run plan
        4. ensure share created
        5. create a second sfs-export with allowed_clients=10.10.10.11 and
        export_path=/vx/abcds-test
        6. create plan and run plan
        7. ensure share created
        Results:
            Shares should be created
        """
        export_path = self.export_path + "test55"
        file_system = "story4154-fs1" + "test55"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test55'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test55'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_export2 = sfs_service + '/exports/ex1_4154_test55_b'
        sfs_export_props2 = "export_path=" + "'" + export_path + "' " + \
                            "ipv4allowed_clients=" + "'" + \
                            self.node1_ip_address + "," + \
                            self.node2_ip_address + "' " + \
                            "export_options=" + "'" "rw,no_root_squash" \
                                                "' " + \
                            "size=" + "'" "10M" "'"
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            self.assertTrue(self.is_sfs_share_present(self.nas_server,
                                                      export_path))
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export2, "sfs-export", sfs_export_props2)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(self.is_sfs_share_present(
                self.nas_server, export_path))
        finally:
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            self.assertTrue(sfs_del)

    @attr('all', 'revert', 'story4154', 'story4154_tc56')
    def obsolete_56_n_create_share_that_already_exists(self):
        """
        Description:
            Test that tries to create a share that already exists with a
            different size
        Steps:
        1. create a share
        2. ensure it is on the sfs
        3. try to create another share wth the same properties other than size
        4. create and run plan
        5. plan should fail
        Results:
            Plan should fail
        """
        export_path = self.export_path + "test56"
        file_system = "story4154-fs1" + "test56"
        sfsservice_url = self.find(self.ms_node, "/infrastructure",
                                   "storage-provider-base",
                                   rtn_type_children=False, find_refs=True)
        sfs_service = sfsservice_url[0] + '/sp1_4154_test56'
        sfs_service_props = "name=" + "'" + self.server_name + "' " + \
                            "management_ipv4=" + "'" + self.sfs_server_ip + \
                            "' " + \
                            "user_name=" + "'" + self.sfs_server_user + \
                            "' " + \
                            "password_key=" + "'" + "key-for-sfs" + "' " + \
                            "pool_name=" + "'" + self.pool_name + "'"
        sfs_virt_serv = sfs_service + '/virtual_servers/vs1_4154_test56'
        sfs_virt_serv_xml = sfs_service + '/virtual_servers'
        sfs_virt_server_props = "name=" + "'" "vsvr1_4154_test56" "' " + \
                                "ipv4address=" + "'" + self.sfs_server_ip + "'"
        sfs_export = sfs_service + '/exports/ex1_4154_test56'
        sfs_export2 = sfs_service + '/exports/ex1_4154_test56_b'
        sfs_export_xml = sfs_service + '/exports'
        sfs_export_props = "export_path=" + "'" + export_path + "' " + \
                           "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "' " + \
                           "export_options=" + "'" "rw,no_root_squash" "' " + \
                           "size=" + "'" "10M" "'"
        sfs_export_props2 = "export_path=" + "'" + export_path + "' " + \
                            "ipv4allowed_clients=" + "'" + \
                            self.node1_ip_address + "' " + \
                            "export_options=" + "'" "rw" "' " + \
                            "size=" + "'" "20M" "'"
        try:
            #1. Create SFS-service
            self.execute_cli_create_cmd(
                self.ms_node, sfs_service, "sfs-service", sfs_service_props)
            # xml test
            self.export_validate_xml(sfs_service, "xml_story4154.xml")
            self.load_xml(sfsservice_url[0], "xml_story4154.xml")
            #2. run litpcrypt
            self.litpcrypt("key-for-sfs", self.sfs_server_user,
                           self.sfs_server_pw)
            #3. create an sfs-virtual-server
            self.execute_cli_create_cmd(
                self.ms_node, sfs_virt_serv, "sfs-virtual-server",
                sfs_virt_server_props)
            # xml test
            self.export_validate_xml(sfs_virt_serv, "xml_story4154.xml")
            self.load_xml(sfs_virt_serv_xml, "xml_story4154.xml")
            #4. create the export
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export, "sfs-export", sfs_export_props)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. Create and run the plan
            self.execute_cli_createplan_cmd(self.ms_node)
            self.execute_cli_runplan_cmd(self.ms_node)
            self.assertTrue(self.wait_for_plan_state(
                self.ms_node, test_constants.PLAN_COMPLETE))
            self.assertTrue(
                self.set_node_connection_data(
                    self.nas_server, username=test_constants.SFS_MASTER_USR,
                    password=test_constants.SFS_MASTER_PW))
            #6. Ensure share was created
            self.assertTrue(self.is_sfs_share_present(self.nas_server,
                                                      export_path))
            self.execute_cli_create_cmd(
                self.ms_node, sfs_export2, "sfs-export", sfs_export_props2)
            # xml test
            self.export_validate_xml(sfs_export, "xml_story4154.xml")
            self.load_xml(sfs_export_xml, "xml_story4154.xml")
            #5. Create and run the plan
            _, stderr, _ = self.execute_cli_createplan_cmd(
                self.ms_node, expect_positive=False)
            self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                            'Create plan failed: Duplicate sfs-export '
                            'defined on sfs-export')
        finally:
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)
            sfs_del = True
            if not self.delete_sfs_shares(self.nas_server, export_path):
                sfs_del = False
            self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                               file_system))
            self.assertTrue(sfs_del)
