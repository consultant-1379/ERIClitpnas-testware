"""
@copyright: Ericsson Ltd
@since:     March 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-6815
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
import test_constants
from xml_utils import XMLUtils


class Story6815(GenericTest):
    """
    LITPCDS-6815:
        As a LITP Installer, I want be able to modify allowed_clients
        list in sfs-export item type to export NAS FS to new node
        in the cluster.
    """

    def setUp(self):
        """Run before every test"""
        super(Story6815, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.ms_ip_address = self.get_node_att(self.ms_node, 'ipv4')
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')
        self.node2_ip_address = self.get_node_att(self.mn_nodes[1], 'ipv4')
        self.nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        self.nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                      "storage", True)
        self.nfs_mount_xml = self.nfsmount_url[0] + '/nfs_mounts'
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.sfs_export_props = "ipv4allowed_clients=" + "'" + \
                                self.node1_ip_address + "' " + \
                                "options=" + "'" "rw,no_root_squash" "' "

    def tearDown(self):
        """Run after every test"""
        super(Story6815, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story6815.xml"):
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

    def inherit(self, path, source_path):
        """
        Method that runs the "inherit" command given passed path and
        source path
        """
        self.execute_cli_inherit_cmd(self.ms_node, path, source_path)

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

    def clean_sfs(self, file_system, path, share_present=True):
        """
        Method that cleans the sfs to it's previous state
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)

        sfs_del = True
        if share_present:
            if not self.delete_sfs_shares(self.nas_server, path):
                sfs_del = False
        self.assertTrue(self.delete_sfs_fs(self.nas_server,
                                           file_system))
        self.assertTrue(sfs_del)

    def check_sfs(self, file_system, path, share_present=True, ip_add=None):
        """
        Method that checks the sfs for existing shares and filesystems
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
        # 7. Ensure items were created
        self.assertTrue(self.is_sfs_filesystem_present(
            self.nas_server, file_system))
        if share_present:
            if ip_add is None:
                self.assertTrue(self.is_sfs_share_present(
                    self.nas_server, path))
            else:
                self.assertTrue(self.is_sfs_share_present(
                    self.nas_server, path, ip_add))

        if not share_present and ip_add is not None:
            self.assertFalse(self.is_sfs_share_present(
                self.nas_server, path, ip_add))

    @attr('all', 'revert', 'story6815', 'story6815_tc01')
    def test_01_p_verify_add_ipv4allowed_client(self):
        """
        This now covers litpcds_6815_tc02
        @tms_id: litpcds_6815_tc01
        @tms_requirements_id: LITPCDS-6815
        @tms_title: verify add ipv4allowed client
        @tms_description: Test that ensures we can add an allowed_client to
        an existing export
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item  under "/infrastructure"
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update ipv4allowed_clients property of sfs-export item
        @result: items updated
        @step: Create and run plan
        @result: plan executes successfully
        @result: new share created
        @step: Remove one of the ipv4allow_clients ipaddresses
        @result: ipaddress removed successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test01"
        path = "/vx/6815-fs1" + test_number
        file_system = "6815-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6815' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'10M'"
        sfs_export = sfs_filesystem + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "'"
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "'"

        self.log("info", "1. Create sfs-filesystem")
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=self.sfs_export_props,
                         xml_path=sfs_export_xml)

        try:
            self.log("info", "2. Create and run plan")
            self.create_plan()

            self.log("info", "3. Ensure the share is created")
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)

            self.log("info", "4. Update the export with another ip")
            self.update_item(sfs_export, item_props=sfs_export_props)

            self.log("info", "5. Create and run plan")
            self.create_plan()

            self.log("info", "6. Ensure share was created")
            self.check_sfs(file_system, path, ip_add=self.node2_ip_address)

            self.log("info", "7. Remove one of the ips from the export")
            self.update_item(sfs_export, item_props=sfs_export_props2)

            self.log("info", "8. Create and run plan")
            self.create_plan()

            self.log("info", "9. Ensure share is removed from sfs")
            self.check_sfs(file_system, path, share_present=False,
                           ip_add=self.node2_ip_address)

        finally:
            self.clean_sfs(file_system, path)

    # attr('all', 'revert', 'story6815', 'story6815_tc02')
    def obsolete_02_p_verify_remove_ipv4allowed_client(self):
        """
        Merged with TC01
        #tms_id: litpcds_6815_tc02
        #tms_requirements_id: LITPCDS-6815
        #tms_title: verify remove ipv4allowed client
        #tms_description: Test that ensures we can remove an allowed_client
        from an existing export
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item  under "/infrastructure"
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update allowed_client property of sfs-export item
        #result: item updated
        #step: Create and run plan
        #result: plan executes successfully
        #result: share is removed from sfs
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story6815', 'story6815_tc03')
    def test_03_p_verify_add_remove_ipv4allowed_client(self):
        """
        @tms_id: litpcds_6815_tc03
        @tms_requirements_id: LITPCDS-6815
        @tms_title: verify add remove ipv4allowed client
        @tms_description: Test that ensures we can remove and add
        allowed_clients to an existing export
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item  under "/infrastructure"
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update allowed_client property of sfs-export item
        @result: item updated
        @step: Create and run plan
        @result: plan executes successfully
        @result: share is removed from sfs
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test03"
        path = "/vx/6815-fs1" + test_number
        file_system = "6815-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6815' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node2_ip_address + "'"

        # 1. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 2. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=self.sfs_export_props,
                         xml_path=sfs_export_xml)

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. Ensure share was created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)
            # 5. Update the export with another ip
            self.update_item(sfs_export, item_props=sfs_export_props)
            # 6. create and run plan
            self.create_plan()
            # 7. ensure share is removed from sfs
            self.check_sfs(file_system, path, share_present=False,
                           ip_add=self.node1_ip_address)
            self.check_sfs(file_system, path, ip_add=self.node2_ip_address)

        finally:
            self.clean_sfs(file_system, path)

    # attr('pre-reg', 'revert', 'story6815', 'story6815_tc04')
    def obsolete_04_n_verify_remove_all_ipv4allowed_client(self):
        """
        Converted to AT "test_04_n_verify_remove_all_ipv4allowed_client.at"
        in nasapi
        #tms_id: litpcds_6815_tc04
        #tms_requirements_id: LITPCDS-6815
        #tms_title: verify remove all ipv4allowed client
        #tms_description: Test that tries to remove all the ips from an export
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item  under "/infrastructure"
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update allowed_client property of sfs-export item to
        empty string
        #result: error thrown: ValidationError
        #result: message shown: Invalid value
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story6815', 'story6815_tc05')
    def obsolete_05_n_verify_order_ipv4allowed_clients(self):
        """
        Converted to AT "test_05_n_verify_order_ipv4allowed_clients.at" in nas
        #tms_id: litpcds_6815_tc05
        #tms_requirements_id: LITPCDS-6815
        #tms_title: verify order ipv4allowed clients
        #tms_description: Test that tries to change the order of ip in the
        allowed clients list
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update allowed_client property of sfs-export item with the same
        ips but in different order
        #result: item updated
        #step: create plan
        #result: error thrown: DoNothingPlanError
        #result: message shown: Create plan failed: no tasks were generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story6815', 'story6815_tc06')
    def obsolete_06_n_remove_client_with_mount(self):
        """
        Converted to AT "test_06_n_remove_client_with_mount.at" in nas
        #tms_id: litpcds_6815_tc06
        #tms_requirements_id: LITPCDS-6815
        #tms_title: remove client with mount
        #tms_description: Test that removes a mounted client from the
        allowed clients list of an export
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        #result: items created
        #step: create nfs-mount item and inherit onto node1
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update allowed_client property of sfs-export item with one ip
        #result: item updated
        #step: create plan
        #result: error thrown: ValidationError
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story6815', 'story6815_tc07')
    def test_07_p_change_all_addresses(self):
        """
        @tms_id: litpcds_6815_tc07
        @tms_requirements_id: LITPCDS-6815
        @tms_title: change all addresses
        @tms_description: Test that ensures we can remove and add all
        allowed_clients to an existing export
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update allowed_client property of sfs-export item with
        two new ips
        @result: item updated
        @step: create and run plan
        @result: plan executes successfully
        @result: old shares removed and new shares created
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test07"
        path = "/vx/6815-fs1" + test_number
        file_system = "6815-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6815' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                            self.ms_ip_address + "," + \
                            "104.32.54.23" + "'"

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

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. Ensure shares are created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)
            self.check_sfs(file_system, path, ip_add=self.node2_ip_address)
            # 5. Update the export with new ips
            self.update_item(sfs_export, item_props=sfs_export_props2)
            # 6. create and run plan
            self.create_plan()
            # 7. ensure shares are removed from sfs
            self.check_sfs(file_system, path, share_present=False,
                           ip_add=self.node1_ip_address)
            self.check_sfs(file_system, path, share_present=False,
                           ip_add=self.node2_ip_address)
            # 8. Ensure new shares are created
            self.check_sfs(file_system, path, ip_add=self.ms_ip_address)
            self.check_sfs(file_system, path, ip_add="104.32.54.23")

        finally:
            self.clean_sfs(file_system, path)

    # attr('pre-reg', 'revert', 'story6815', 'story6815_tc08')
    def obsolete_08_n_repeated_ipaddress(self):
        """
        Converted to AT in "test_08_n_repeated_ipaddress.at" in nasapi
        #tms_id: litpcds_6815_tc08
        #tms_requirements_id: LITPCDS-6815
        #tms_title: duplicate ipaddress
        #tms_description: Test that tries to duplicate an ip
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update allowed_client property of sfs-export item with
        three new ips, two existing ips with one duplication
        #result: error thrown: ValidationError
        #result: message shown: Duplicate IP address detected
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story6815', 'story6815_tc09')
    def test_09_p_add_client_with_mount(self):
        """
        @tms_id: litpcds_6815_tc09
        @tms_requirements_id: LITPCDS-6815
        @tms_title: add client with mount
        @tms_description: Test that adds a new client to an export and
        mounts to it
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update allowed_client property of sfs-export item with
        two ips
        @result: item updated
        @step: create nfs-mount under "/infrastructure" and inherit onto
        node 1
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @result: share created and mount in /fstab
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test09"
        path = "/vx/6815-fs1" + test_number
        file_system = "6815-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6815' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node2_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "' "
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_6815' +\
                    test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/6815test9" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_6815' + \
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

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. Ensure share was created
            self.check_sfs(file_system, path, ip_add=self.node2_ip_address)
            # 5. Update the export with another ip
            self.update_item(sfs_export, item_props=sfs_export_props2)
            # 6. create an nfs-mount on node
            self.create_item(item_path=nfs_mount,
                             item_type="nfs-mount",
                             item_props=nfs_mount_props,
                             xml_path=self.nfs_mount_xml)
            # 7. inherit mount to node
            self.inherit(path=node_file_system, source_path=nfs_mount)
            # 8. Create and run the plan
            self.create_plan()
            # 9. Ensure share was created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)
            # 10. check for mount in fstab
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story6815', 'story6815_tc10')
    def test_10_p_remove_and_modify_allowed_clients(self):
        """
        @tms_id: litpcds_6815_tc10
        @tms_requirements_id: LITPCDS-6815
        @tms_title: remove and modify allowed clients
        @tms_description: Test that adds a new client to an export
        and mounts to it
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item  under "/infrastructure" with two ip
        values in ipv4allowed_clients property
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update allowed_client property of sfs-export item with
        two ips, one of which is new
        @result: item updated
        @step: create nfs-mount under "/infrastructure" and inherit onto
        node 1
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @result: share created and mount in /fstab
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test10"
        path = "/vx/6815-fs1" + test_number
        file_system = "6815-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6815' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_6815' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "," + \
                           self.ms_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           "41.36.25.154" + "' "
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_6815' +\
                    test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_6815' + \
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
        # 3. create an nfs-mount on node
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props,
                         xml_path=self.nfs_mount_xml)
        # 4. inherit mount to node
        self.inherit(path=node_file_system, source_path=nfs_mount)

        try:
            # 5. Create and run the plan
            self.create_plan()
            # 6. Ensure shares was created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)
            self.check_sfs(file_system, path, ip_add=self.node2_ip_address)
            self.check_sfs(file_system, path, ip_add=self.ms_ip_address)
            # 7. check for mount in fstab
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])
            # 8. Update the export with another ip
            self.update_item(sfs_export, item_props=sfs_export_props2)
            # 9. Create and run the plan
            self.create_plan()
            # 10. Ensure share was created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)
            self.check_sfs(file_system, path, ip_add="41.36.25.154")
            # 11. check for mount in fstab
            self.check_mount_in_fstab(file_system, path, self.mn_nodes[0])

        finally:
            self.clean_sfs(file_system, path)
