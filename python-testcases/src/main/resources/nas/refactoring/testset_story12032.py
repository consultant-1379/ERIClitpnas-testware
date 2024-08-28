"""
@copyright: Ericsson Ltd
@since:     November 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-12032
"""
from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils
from storage_utils import StorageUtils
import test_constants


class Story12032(GenericTest):
    """
    LITPCDS-12032:
        As a litp user I want to be able to update the nfs-mount
        to be a different sfs-virtual-server item as a provider
    """

    def setUp(self):
        """Run before every test"""
        super(Story12032, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.virtual_servers = self.find(self.ms_node, "/infrastructure",
                                         "collection-of-sfs-virtual-server")
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.nodes_url = self.find(self.ms_node, "/deployments", "node", True)

    def tearDown(self):
        """Run after every test"""
        super(Story12032, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story12032.xml"):
        """
        Description
            Exports the created item to xml file and Validates the xml file
            It then loads the xml and expects the correct error
        Actions:
            1: run export command on item path
            2: validate the xml file
            @step: Loads the xml
        @result:
            @step: Expects an error
        @result:
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
            self.assertTrue(self.wait_for_plan_state(node, plan_outcome,
                                                     timeout_mins=50))

    def inherit(self, path, source_path):
        """
        Method that runs the "inherit" command given passed path and
        source path
        """
        self.execute_cli_inherit_cmd(self.ms_node, path, source_path)

    def check_mount_in_fstab(self, item2grep, mnt_path, node=None):
        """
        Ensures mounted filesystem entry in fstab
        """
        node = node or self.ms_node
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

    def clean_sfs(self, file_system, path=None):
        """
        Method that cleans the sfs to it's previous state
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        sfs_del = True
        if path is not None:
            if not self.delete_sfs_shares(self.nas_server, path):
                sfs_del = False

        self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                           file_system))
        self.assertTrue(sfs_del)

    @attr('pre-reg', 'revert', 'story12032', 'story12032_tc01')
    def test_01_p_update_nfs_mount_provider_to_vip(self):
        """
        #tms_id: litpcds_12032_tc01
        #tms_requirements_id: LITPCDS-12032
        #tms_title: update nfs mount provider
        #tms_description:
            Test that ensures we can update the provider of an nfs-mount from
            one sfs-virtual-server to another
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create an sfs-virtual-server, name = vsvr2
        #result: item created in model
        #step: create an nfs-mount (1), provider = vsvr1
        #result: item created in model
        #step: create an nfs-mount (2), provider = vsvr2
        #result: item created in model
        #step: inherit mount1 to node1
        #result: item created in model
        #step: inherit mount2 to node2
        #result: item created in model
        #step: create and run plan
        #result: plan runs to success
        #step: check the fs tab to ensure entries are correct
        #result: entries as expected
        #step: update the nfs-mount 1 to provider = vsvr2
        #result: model is updated
        #step: update the nfs-mount 2 to provider = vsvr1
        #result: model is updated
        #step: create and run plan
        #result: plan runs to success
        #step: check the fs tab to ensure entries are correct
        #result: entries as expected
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        test_number = "_test01"
        file_system = "12032-fs1_a" + test_number
        path = "/vx/" + file_system
        vsvr1 = "vsvr1_12032" + test_number
        vsvr2 = "virtserv1"
        vips = self.get_node_att('nas4', 'vips')
        sfs_virt_serv_1 = self.virtual_servers[0] + '/vs1_12032' + test_number
        sfs_virt_server_props_1 = "name=" + "'" + vsvr1 + "' " + \
                                  "ipv4address=" + "'" + \
                                  vips['2'] + "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_12032' \
                                           + test_number
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export = sfs_filesystem + '/exports/ex1_12032_b' + test_number
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           "192.168.0.0/16" + "' " + \
                           "options=" + "'" "rw,no_root_squash" "'"
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_1 = nfsmount_url[0] + '/nfs_mounts/nm1_12032' + test_number
        nfs_mount_props_1 = "export_path=" "'" + path + "' " + \
                            "network_name=" "'" "mgmt" "' " + \
                            "provider=" "'" + vsvr1 + "' " + \
                            "mount_options=" "'" "soft" "' " + \
                            "mount_point=" + "'" + "/test1" + "'"
        nfs_mount_2 = nfsmount_url[0] + '/nfs_mounts/nm2_12032' + test_number
        nfs_mount_props_2 = "export_path=" "'" + path + "' " + \
                            "network_name=" "'" "mgmt" "' " + \
                            "provider=" "'" + vsvr2 + "' " + \
                            "mount_options=" "'" "soft" "' " + \
                            "mount_point=" + "'" + "/test1" + "'"
        nfs_mount_props_3 = "provider=" "'" + vsvr2 + "'"
        nfs_mount_props_4 = "provider=" "'" + vsvr1 + "'"
        node_file_system1 = self.nodes_url[0] + '/file_systems/nm1_12032' + \
                                                test_number
        node_file_system2 = self.nodes_url[1] + '/file_systems/nm2_12032' + \
                                                test_number

        # 1. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 2. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml)
        # 3. create an sfs-virtual-server, name = vsvr1
        self.create_item(item_path=sfs_virt_serv_1,
                         item_type="sfs-virtual-server",
                         item_props=sfs_virt_server_props_1,
                         xml_path=self.virtual_servers[0])
        # 4. create an nfs-mount (1), provider = vsvr1
        self.create_item(item_path=nfs_mount_1,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props_1,
                         xml_path=nfs_mount_xml)
        # 5. create an nfs-mount (2), provider = vsvr2
        self.create_item(item_path=nfs_mount_2,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props_2,
                         xml_path=nfs_mount_xml)
        # 6. inherit mount1 to node1
        self.inherit(path=node_file_system1, source_path=nfs_mount_1)
        # 7. inherit mount2 to node2
        self.inherit(path=node_file_system2, source_path=nfs_mount_2)
        try:
            # 8. create and run plan
            self.create_plan()
            # 9. check the fs tab to ensure entries are correct
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[1])
            # 10. update the nfs-mount 1 to provider = vsvr2
            self.update_item(item_path=nfs_mount_1,
                             item_props=nfs_mount_props_3)
            # 11. update the nfs-mount 2 to provider = vsvr1
            self.update_item(item_path=nfs_mount_2,
                             item_props=nfs_mount_props_4)
            # 12. create and run plan
            self.create_plan()
            # 13. check the fs tab to ensure entries are correct
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[1])

        finally:
            self.clean_sfs(file_system, path)

    # attr('all', 'revert', 'story12032', 'story12032_tc02')
    def test_02_n_update_nfs_mounts_provider_to_incorrect_values(self):
        """
        Converted to AT
        "test_02_n_update_nfs_mounts_provider_to_incorrect_values.at" in nas
        #tms_id: litpcds_12032_tc02
        #tms_requirements_id: LITPCDS-12032
        #tms_title: update nfs mount provider
        #tms_description:
            Test that ensures you can't update an nfs-mount's provider to
            an invalid value
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an nfs-service, name = NFS1
        #result: item created in model
        #step: create an nfs-mount (1), provider = VIP1
        #result: item created in model
        #step: create an nfs-mount (2), provider = NFS1
        #result: item created in model
        #step: create and run plan
        #result: plan runs to success
        #step: update the nfs-mount 1 to provider = NFS1
        #result: entries as expected
        #step: create_plan and ensure the correct error is thrown
        #result: expected error thrown
        #step: update the nfs-mount 2 to provider = VIP1
        #result: model is updated
        #step: create_plan and ensure the correct error is thrown
        #result: expected error thrown
        #step: update the nfs-mount 1 to provider = "non-existent"
        #result: model is updated
        #step: create_plan and ensure the correct error is thrown
        #result: expected error thrown
        #step: create an nfs-service, name = NFS2
        #result: item created in model
        #step: remove NFS1
        #result: model is updated
        #step: create an nfs-mount (2), provider = NFS2
        #result: item created in model
        #step: create_plan and ensure the correct error is thrown
        #result: expected error thrown
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story12032', 'story12032_tc03')
    def test_03_p_update_nodes_ip_and_update_mount(self):
        """
        #tms_id: litpcds_12032_tc03
        #tms_requirements_id: LITPCDS-12032
        #tms_title: update nfs mount provider
        #tms_description:
          Test that updates a nodes IP and updates a provider of
          mount mounted to the node in the same plan.
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create an sfs-virtual-server, name = vsvr1
        #result: item created in model
        #step: create an nfs-mount (1), provider = vsvr1
        #result: item created in model
        #step: create an nfs-mount (2), provider = vsvr2
        #result: item created in model
        #step: inherit mount1 to node1
        #result: item created in model
        #step: inherit mount2 to node2
        #result: item created in model
        #step: create and run plan
        #result: plan runs to success
        #step: check the fs tab to ensure entries are correct
        #result: entries as expected
        #step: update the nfs-mount 1 to provider = vsvr2 and network_name
        #result: model is updated
        #step: update the nfs-mount 2 to provider = vsvr1 and network_name
        #result: model is updated
        #step: update the allowed clients list to include the new ip
        #result: model is updated
        #step: update node1's ip
        #result: model is updated
        #step: update node2's ip
        #result: model is updated
        #step: create and run plan
        #result: plan runs to success
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        node_url = self.nodes_url[0] + '/network_interfaces/br0'
        node_url2 = self.nodes_url[1] + '/network_interfaces/br0'
        test_number = "_test03"
        file_system = "12032-fs1_a" + test_number
        path = "/vx/" + file_system
        vsvr1 = "vsvr1_12032" + test_number
        vsvr2 = "virtserv1"
        vips = self.get_node_att('nas4', 'vips')
        sfs_virt_serv_1 = self.virtual_servers[0] + '/vs1_12032' + test_number
        sfs_virt_server_props_1 = "name=" + "'" + vsvr1 + "' " + \
                                  "ipv4address=" + "'" + \
                                  vips['2'] + "'"
        nfsmount_url = self.find(self.ms_node, "/infrastructure", "storage",
                                 True)
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_12032' \
                                           + test_number
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export = sfs_filesystem + '/exports/ex1_12032_b' + test_number
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           "192.168.0.0/16,172.16.100.0/24," \
                           "172.16.200.0/24" + "' " + \
                           "options=" + "'" "rw,no_root_squash" "'"
        nfs_mount_xml = nfsmount_url[0] + '/nfs_mounts'
        nfs_mount_1 = nfsmount_url[0] + '/nfs_mounts/nm1_12032' + test_number
        nfs_mount_props_1 = "export_path=" "'" + path + "' " + \
                            "network_name=" "'" "mgmt" "' " + \
                            "provider=" "'" + vsvr1 + "' " + \
                            "mount_options=" "'" \
                            "soft,clientaddr='192.168.0.43'" "' " + \
                            "mount_point=" + "'" + "/test1" + "'"
        nfs_mount_2 = nfsmount_url[0] + '/nfs_mounts/nm2_12032' + test_number
        nfs_mount_props_2 = "export_path=" "'" + path + "' " + \
                            "network_name=" "'" "mgmt" "' " + \
                            "provider=" "'" + vsvr2 + "' " + \
                            "mount_options=" "'" "soft" "' " + \
                            "mount_point=" + "'" + "/test1" + "'"
        nfs_mount_props_3 = "provider=" "'" + vsvr2 + "' " + \
                            "network_name=" "'" + "traffic1" + "'"
        nfs_mount_props_4 = "provider=" "'" + vsvr1 + "' " + \
                            "network_name=" "'" + "traffic2" + "'"
        node_file_system1 = self.nodes_url[0] + '/file_systems/nm1_12032' + \
                                                test_number
        node_file_system2 = self.nodes_url[1] + '/file_systems/nm2_12032' + \
                                                test_number
        new_ip = "ipaddress=192.168.0.45"
        old_ip = "ipaddress=192.168.0.43"
        new_ip2 = "ipaddress=192.168.0.46"
        old_ip2 = "ipaddress=192.168.0.44"
        new_provider = "provider=" "'" + vsvr1 + "'"
        old_provider = "provider=" "'" + vsvr2 + "'"
        managed_path = self.find(self.ms_node, "/infrastructure",
                                 "sfs-export")
        new_allowed_clients = "ipv4allowed_clients=192.168.0.43," \
                              "192.168.0.44,192.168.0.45,192.168.0.46," \
                              "172.16.0.0/16"

        # 1. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 2. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml)
        # 3. create an sfs-virtual-server, name = vsvr1
        self.create_item(item_path=sfs_virt_serv_1,
                         item_type="sfs-virtual-server",
                         item_props=sfs_virt_server_props_1,
                         xml_path=self.virtual_servers[0])
        # 4. create an nfs-mount (1), provider = vsvr1
        self.create_item(item_path=nfs_mount_1,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props_1,
                         xml_path=nfs_mount_xml)
        # 5. create an nfs-mount (2), provider = vsvr2
        self.create_item(item_path=nfs_mount_2,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props_2,
                         xml_path=nfs_mount_xml)
        # 6. inherit mount1 to node1
        self.inherit(path=node_file_system1, source_path=nfs_mount_1)
        # 7. inherit mount2 to node2
        self.inherit(path=node_file_system2, source_path=nfs_mount_2)
        try:
            # 8. create and run plan
            self.create_plan()
            # 9. check the fs tab to ensure entries are correct
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[1])
            # 10. update the nfs-mount 1 to provider = vsvr2 and network_name
            self.update_item(item_path=nfs_mount_1,
                             item_props=nfs_mount_props_3)
            # 11. update the nfs-mount 2 to provider = vsvr1 and network_name
            self.update_item(item_path=nfs_mount_2,
                             item_props=nfs_mount_props_4)
            # 12. update the allowed clients list to include the new ip
            self.update_item(item_path=managed_path[1],
                             item_props=new_allowed_clients)
            # 13. update the node1's ip
            self.update_item(item_path=node_url,
                             item_props=new_ip)
            # 14. update the node2's ip
            self.update_item(item_path=node_url2,
                             item_props=new_ip2)
            self.update_item(item_path="/deployments/d1/clusters/c1/"
                                       "nodes/n1/file_systems/mfs2",
                             item_props=new_provider)
            # 15. create and run plan
            self.create_plan()

        finally:
            self.update_item(item_path=node_url,
                             item_props=old_ip)
            self.update_item(item_path=node_url2,
                             item_props=old_ip2)
            self.update_item(item_path="/deployments/d1/clusters/c1/"
                                       "nodes/n1/file_systems/mfs2",
                             item_props=old_provider)
            self.clean_sfs(file_system, path)
