"""
@copyright: Ericsson Ltd
@since:     February 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-8524
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
from litp_security_utils import SecurityUtils
import test_constants
from xml_utils import XMLUtils


class Story8524(GenericTest):
    """
    LITPCDS-8524:
        As a LITP Installer, I want to be able to create a
        filesystem & shares on SFS so that they are available to be mounted
    """

    def setUp(self):
        """Run before every test"""
        super(Story8524, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.security = SecurityUtils()
        self.sfs_server_ip = self.get_node_att(self.nas_server, "ipv4")
        self.ms_ip_address = self.get_node_att(self.ms_node, 'ipv4')
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')
        self.node2_ip_address = self.get_node_att(self.mn_nodes[1], 'ipv4')
        self.nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        self.sfs_service_url = self.find(self.ms_node, "/infrastructure",
                                         "storage-provider-base",
                                         rtn_type_children=False,
                                         find_refs=True)
        self.nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                      "storage", True)
        self.nfs_mount_xml = self.nfsmount_url[0] + '/nfs_mounts'
        self.sfs_services = self.find(self.ms_node, "/infrastructure",
                                "sfs-service")
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.sfs_export_props = "ipv4allowed_clients=" + "'" + \
                                self.node1_ip_address + "' " + \
                                "options=" + "'" "rw,no_root_squash" "' "

    def tearDown(self):
        """Run after every test"""
        super(Story8524, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story8524.xml"):
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

    def litpcrypt(self, key, user_input, password_input):
        """
        Creates and runs a litpcrypt command
        """
        cmd = self.security.get_litpcrypt_set_cmd(service=key,
                                                  user=user_input,
                                                  password=password_input)
        out, err, ret_code = self.run_command(self.ms_node, cmd)
        # expect no output
        self.assertEqual([], out)
        # expect no error
        self.assertEqual([], err)
        # expect the return code to equal 0
        self.assertEqual(0, ret_code)

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

    @attr('all', 'revert', 'story8524', 'story8524_tc01')
    def test_01_p_ensure_filesystem_created(self):
        """
        @tms_id: litpcds_8524_tc01
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that ensures we can create a filesystem
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: Create and run the plan
        @result: plan runs to success
        @step: Ensure filesystem was created
        @result: filesystems created as expected
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test01"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"

        # 1. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        try:
            # 2. Create and run the plan
            self.create_plan()
            # 3. Ensure filesystem was created
            self.check_sfs(file_system, path, share_present=False)
        finally:
            self.clean_sfs(file_system, path, share_present=False)

    @attr('all', 'revert', 'story8524', 'story8524_tc02')
    def test_02_p_ensure_share_created(self):
        """
        @tms_id: litpcds_8524_tc02
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that ensures we can create a export
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: create an sfs-export
        @result: item created in model
        @step: Create and run the plan
        @result: plan runs to success
        @step: Ensure share was created
        @result: share created as expected
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test02"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'

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
            self.check_sfs(file_system, path)
        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8524', 'story8524_tc03')
    def test_03_p_create_two_exports_with_different_allowed_clients(self):
        """
        @tms_id: litpcds_8524_tc03
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates 2 exports with different allowed clients
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: create an sfs-export
        @result: item created in model
        @step: create and run plan
        @result: plan runs to success
        @step: ensure share created
        @result: share created as expected
        @step: create a second sfs-export
        @result: item created in model
        @step: create plan and run plan
        @result: plan runs to success
        @step: ensure share created
        @result: share created as expected
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test03"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.ms_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export2 = sfs_filesystem + '/exports/ex2_8524' + test_number

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
            self.check_sfs(file_system, path, ip_add=self.ms_ip_address)
            # 5. create a second sfs-export
            self.create_item(item_path=sfs_export2,
                            item_type="sfs-export",
                            item_props=self.sfs_export_props,
                            xml_path=sfs_export_xml)
            # 6. create plan and run plan
            self.create_plan()
            # 7. ensure share created
            self.check_sfs(file_system, path, ip_add=self.node1_ip_address)

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8524', 'story8524_tc04')
    def test_04_p_create_export_and_mount(self):
        """
        @tms_id: litpcds_8524_tc04
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates an export and a mount
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: Create an sfs-export
        @result: item created in model
        @step: Create an nfs-mount on node
        @result: item created in model
        @step: inherit mount to node
        @result: item created in model
        @step: create and run plan
        @result: plan runs to success
        @step: ensure mount is successful on the node
        @result: mount created as expected
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test04"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number

        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_8524' + test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_8524' + \
                           test_number

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
        # 3. Create an nfs-mount on node
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props,
                         xml_path=self.nfs_mount_xml)
        # 4. inherit mount to node
        self.inherit(path=node_file_system, source_path=nfs_mount)

        try:
            # 5. run plan and check finishes with success
            self.create_plan()
            self.check_sfs(file_system=file_system,
                           path=path,
                           ip_add=self.node1_ip_address)
            # 6. check for mount in fstab
            self.check_mount_in_fstab(file_system, path,
                                      self.mn_nodes[0])
        finally:
            self.clean_sfs(file_system=file_system,
                           path=path)

    @attr('all', 'revert', 'story8524', 'story8524_tc05')
    def test_05_p_create_exports_and_one_mount(self):
        """
        @tms_id: litpcds_8524_tc05
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates multiple exports but mounts to one
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created as expected
        @step: Create an sfs-export with allowed_clients containing node1
        @result: item created in model
        @step: create an sfs-export with allowed_clients not containing node1
        @result: item created in model
        @step: Create an nfs-mount on node1
        @result: item created in model
        @step: inherit mount to node
        @result: item created in model
        @step: create and run plan
        @result: plan runs to success
        @step: ensure creates 1 filesystem and 2 exports
        @result: items created as expected
        @step: ensure mount is successful on the node
        @result: node1 has expected mount
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test05"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export2 = sfs_filesystem + '/exports/ex2_8524' + test_number
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                            self.node2_ip_address + "' " + \
                            "options=" + "'" "rw,no_root_squash" "' "
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_8524' + test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_8524' + \
                           test_number

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
        # 3. create another sfs-export
        self.create_item(item_path=sfs_export2,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml)
        # 4. Create an nfs-mount on node
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props,
                         xml_path=self.nfs_mount_xml)
        # 5. inherit mount to node
        self.inherit(path=node_file_system, source_path=nfs_mount)

        try:
            # 6. check plan finished with success
            self.create_plan()
            # 7. ensure creates 1 filesystem and 2 exports
            self.check_sfs(file_system=file_system,
                           path=path,
                           share_present=False)
            self.check_sfs(file_system=file_system,
                           path=path,
                           ip_add=self.node1_ip_address)
            self.check_sfs(file_system=file_system,
                           path=path,
                           ip_add=self.node2_ip_address)
            # 8. ensure mount is successful on the node
            self.check_mount_in_fstab(file_system, path,
                                      self.mn_nodes[0])
        finally:
            self.clean_sfs(file_system=file_system,
                           path=path)

    @attr('all', 'revert', 'story8524', 'story8524_tc06')
    def test_06_p_create_export_and_mount_with_multiple_ips(self):
        """
        @tms_id: litpcds_8524_tc06
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates an export with multiple ips
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: Create an sfs-export
        @result: item create in model
        @step: Create an nfs-mount
        @result: item created in model
        @step: inherit mount to node
        @result: item created in model
        @step: check plan finished with successcreate and run plan
        @result: plan runs to success
        @step: Check 1 filesystem and 2 exports created
        @result: expected items created
        @step: ensure mount is successful on node 1
        @result: mount created as expected
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test06"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           self.node1_ip_address + "," + \
                           self.node2_ip_address + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_8524' + test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_8524' + \
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
        # 3. Create an nfs-mount on node
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props,
                         xml_path=self.nfs_mount_xml)
        # 4. inherit mount to node
        self.inherit(path=node_file_system, source_path=nfs_mount)

        try:
            # 5. check plan finished with success
            self.create_plan()
            # 6. ensure creates 1 filesystem and 2 exports
            self.check_sfs(file_system=file_system,
                           path=path,
                           share_present=False)
            self.check_sfs(file_system=file_system,
                           path=path,
                           ip_add=self.node1_ip_address)
            self.check_sfs(file_system=file_system,
                           path=path,
                           ip_add=self.node2_ip_address)
            # 7. ensure mount is successful on the node
            self.check_mount_in_fstab(file_system, path,
                                      self.mn_nodes[0])
        finally:
            self.clean_sfs(file_system=file_system,
                           path=path)

    @attr('all', 'revert', 'story8524', 'story8524_tc07')
    def test_07_p_create_filesystem_and_share_that_exist_on_sfs(self):
        """
        @tms_id: litpcds_8524_tc07
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates a filesystem and export that already
            exist on the sfs
        @tms_test_steps:
        @step: create filesystem and share directly on the sfs
        @result: filesystems created and shared on SFS server
        @step: create an sfs-filesystem
        @result: item created in model
        @step: Create an sfs-export
        @result: item created in model
        @step: create and run plan
        @result: plan completes to success
        @step: ensure share created on  sfs
        @result: expected items present on sfs
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test07"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'

        self.assertTrue(
            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW))
        # 1. create filesystem and share directly on the sfs
        self.assertTrue(self.create_sfs_fs(
            self.nas_server, file_system, fs_option="simple",
            fs_size="10M", sfs_pool="litp2"))
        self.assertTrue(
            self.create_sfs_share(self.nas_server, path, "rw,no_root_squash",
                                  share_ipaddrs=self.node1_ip_address))
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 3. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=self.sfs_export_props,
                         xml_path=sfs_export_xml)
        try:
            # 4. Create and run the plan
            self.create_plan()
            # 5. Ensure share was created
            self.check_sfs(file_system, path)
        finally:
            self.clean_sfs(file_system=file_system,
                           path=path)

    #@attr('all', 'revert', 'story8524', 'story8524_tc08')
    def obsolete_08_n_create_duplicate_vip(self):
        """
        Converted to AT "test_08_n_create_duplicate_vip.at" in nas
        #tms_id: litpcds_8524_tc08
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates duplicate virtual servers
        #tms_test_steps:
        #step: create an sfs virtual server with same ip as existing
        #result: item created in the model
        #step:  run create_plan
        #result: create_plan should fail with expected message
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc09')
    def obsolete_09_n_invalid_vip_name(self):
        """
        Converted to AT "test_09_n_invalid_vip_name.at" in nasapi
        #tms_id: litpcds_8524_tc09
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates a vip with an invalid name
        #tms_test_steps:
        #step: Create an sfs virtual server with an invalid name
        #result: expected validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc10')
    def obsolete_10_n_invalid_vip_ipv4address(self):
        """
        Converted to AT "test_10_n_invalid_vip_ipv4address.at" in nasapi
        #tms_id: litpcds_8524_tc10
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates a vip with an invalid ipv4address
        #tms_test_steps:
        #step: Create an sfs virtual server with an invalid ipv4address
        #result: ensure the item creation fails with the correct error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc11')
    def obsolete_11_n_create_duplicate_services(self):
        """
        Converted to AT "test_11_n_create_duplicate_services.at" in nas
        #tms_id: litpcds_8524_tc11
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates two sfs-services with the same ip
        #tms_test_steps:
        #step: Create an sfs-service with the same ip as an existing server
        #result: item created in the model
        #step: run create_plan
        #result: create_plan fails with expected validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc12')
    def obsolete_12_n_login_details_must_exist(self):
        """
        Converted to AT "test_12_n_login_details_must_exist.at" in nasapi
        #tms_id: litpcds_8524_tc12
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-service without the login details
        #tms_test_steps:
        #step: create an sfs-service without specifying the login details
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc13')
    def obsolete_13_n_create_service_with_invalid_key(self):
        """
        Converted to AT "test_13_n_create_service_with_invalid_key.at" in nas
        #tms_id: litpcds_8524_tc13
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-service with an invalid key
        #tms_test_steps:
        #step: create an sfs-service with key not in keystore
        #result: item created in model
        #step: run litpcrypt
        #result: command executes successfully
        #step: create an sfs-pool
        #result: item created in model
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: run create plan
        #result: expected validation error outputgenerated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc14')
    def obsolete_14_n_create_service_with_invalid_user(self):
        """
        Converted to AT "test_14_n_create_service_with_invalid_user.at" in
        nasapi
        #tms_id: litpcds_8524_tc14
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-service with an invalid user
        #tms_test_steps:
        #step: create an sfs-service with user not in keystore but a valid key
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc15')
    def obsolete_15_n_create_an_sfs_service_with_user_does_not_exist(self):
        """
        Description:
            Test that creates a SFS service with an incorrect
            username property
        Steps:
        1. create an sfs-service whereby user does not exist on the SFS
        2. run litpcrypt
        3. create an sfs-pool
        4. create an sfs-filesystem
        5. create an sfs-export
        6. create and run plan
        7. check /var/log/messages for correct error
        Results:
            Create plan should fail
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc16')
    def obsolete_16_n_create_duplicate_pools(self):
        """
        Converted to AT "test_16_n_create_duplicate_pools.at" in nas
        #tms_id: litpcds_8524_tc16
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates duplicate sfs-pools
        #tms_test_steps:
        #step: create an sfs-pool with the same name as an existing pool
        #result: item created in model
        #step: create an sfs-filesystem
        #result: item created ijn model
        #step: create an sfs-export
        #result: item created in model
        #step: run create_plan
        #result: create_plan fails with expected validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc17')
    def obsolete_17_n_pool_must_exist(self):
        """
        Converted to AT "test_17_n_pool_must_exist.at" in nasapi
        #tms_id: litpcds_8524_tc17
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that checks an error is given when creating a filesystem
            under a sfs-service
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: creation fails with expected validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc18')
    def obsolete_18_n_pool_name_required(self):
        """
        Converted to AT "test_18_n_pool_name_required.at" in nasapi
        #tms_id: litpcds_8524_tc18
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-pool without the pool_name property
        #tms_test_steps:
        #step: create an sfs-pool without the pool_name property
        #result: ensure item creation fails with correct error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc19')
    def obsolete_19_n_invalid_pool_name(self):
        """
        Converted to AT "test_19_n_invalid_pool_name.at" in nasapi
        #tms_id: litpcds_8524_tc19
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-pool with an invalid pool_name
        #tms_test_steps:
        #step: create an sfs-pool with an invalid pool_name property
        #result: ensure item creation fails with correct error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc20')
    def obsolete_20_n_invalid_pool_name_length(self):
        """
        Converted to AT "test_20_n_invalid_pool_name_length.at" in nasapi
        #tms_id: litpcds_8524_tc20
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-pool with an invalid pool_name
        #tms_test_steps:
        #step: create an sfs-pool with an invalid pool_name property
        #result: ensure item creation fails with correct error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('pre-reg', 'revert', 'story8524', 'story8524_tc21')
    def obsolete_21_n_create_invalid_pool_name(self):
        """
        Test has been made obsolete due to story 10974 being implemented.
        this functionality is being tested inside the following
        unit test:
        test_fs_resize_callback
        Description:
            Test that creates an sfs-pool with an invalid pool_name
        Steps:
        1. create an sfs-service
        2. run litpcrypt
        3. create an sfs-pool with an invalid pool_name property
        4. create an sfs-filesystem
        5. create an sfs-export
        6. Create and run the plan
        7. check /var/log/messages for expected error logs
        Results:
            Should fail to create item
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc22')
    def obsolete_22_n_create_duplicate_filesystems(self):
        """
        Converted to AT "test_22_n_create_duplicate_filesystems.at" in nas
        #tms_id: litpcds_8524_tc22
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Tests user cannot create duplicate filesystems
        #tms_test_steps:
        #step: Create an SFS-filesystem
        #result: item created in model
        #step: Create a second sfs filesystem with the same path property
        #result: item created in model
        #step: run create_plan
        #result: creation fails with expected validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc24')
    def obsolete_24_n_filesystem_must_exist(self):
        """
        Converted to AT "test_24_n_filesystem_must_exist.at" in nasapi
        #tms_id: litpcds_8524_tc24
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export under an sfs-pool
        #tms_test_steps:
        #step: create an sfs-export under the pool
        #result: creation fails with InvalidLocationError
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc25')
    def obsolete_25_n_filesystem_requires_size(self):
        """
        Converted to AT "test_25_n_filesystem_requires_size.at" in nasapi
        #tms_id: litpcds_8524_tc25
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an sfs-filesystem without the
            "size" parameter
        #tms_test_steps:
        #step: create an sfs-filesystem without "size"
        #result: item creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story8524', 'story8524_tc26')
    def test_26_n_create_filesystem_with_size_larger_than_pool(self):
        """
        @tms_id: litpcds_8524_tc26
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that user cannot create file system greater than available
            space
        @tms_test_steps:
        @step: create an sfs-filesystem of 5000GB size
        @result: item created in model
        @step: run create_plan
        @result: creation fails with validation error
        @step: check /var/log/messages for expected error
        @result: expected error found in logs
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test26"
        path = "/vx/8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "5000G" "'"
        expected_error_logs = ['Unable to create fs 8524-fs1_test26'
                               ' due to either insufficient space/unavailable'
                               ' disk']

        # 1. create an sfs-filesystem and expect the correct error
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 2. Create and run the plan
        self.create_plan(plan_outcome=test_constants.PLAN_FAILED)
        # 3. check /var/log/messages for expected error logs
        self.grep_logs(expected_error_logs)

    #@attr('all', 'revert', 'story8524', 'story8524_tc27')
    def obsolete_27_n_filesystem_valid_size_start(self):
        """
        Converted to AT "test_27_n_filesystem_valid_size_start.at" in nasapi
        #tms_id: litpcds_8524_tc27
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creation fails for sfs-filesystems with invalid
            sizes
        #tms_test_steps:
        #step: create an sfs-filesystem with zero size
        #result: creation fails with expected error
        #step: create an sfs-filesystem with invalid size unit
        #result: creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc28')
    def obsolete_28_n_filesystem_valid_size_end(self):
        """
        Converted to AT "test_28_n_filesystem_valid_size_end.at" in nasapi
        #tms_id: litpcds_8524_tc28
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that attempts to create sfs-filesystem with invalid
            sizes
        #tms_test_steps:
        #step: create an sfs-filesystem with invalid size
        #result: creation fails with expected validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc29')
    def obsolete_29_n_filesystem_requires_path(self):
        """
        Converted to AT "test_29_n_filesystem_requires_path.at" in nasapi
        #tms_id: litpcds_8524_tc29
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates sfs-filesystems without a path
        #tms_test_steps:
        #step: create an sfs-filesystem without a path
        #result: creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc30')
    def obsolete_30_n_filesystem_with_invalid_path_character(self):
        """
        Converted to AT "test_30_n_filesystem_with_invalid_path_character.at"
        in nasapi
        #tms_id: litpcds_8524_tc30
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates sfs-filesystems with an invalid
            path character
        #tms_test_steps:
        #step: create an sfs-filesystem with an invalid "path"
               charachters
        #result: creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc31')
    def obsolete_31_n_filesystem_path_over_max_length(self):
        """
        Converted to AT "test_31_n_filesystem_path_over_max_length.at" in
        nasapi
        #tms_id: litpcds_8524_tc31
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates sfs-filesystems with a "path"
            that's too long
        #tms_test_steps:
        #step: create an sfs-filesystem with an path over the maximum length
        #result: creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc32')
    def obsolete_32_n_filesystem_with_incorrect_prefix(self):
        """
        Converted to AT "test_32_n_filesystem_with_incorrect_prefix.at" in
        nasapi
        #tms_id: litpcds_8524_tc32
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates sfs-filesystems with a "path"
            that's too long
        #tms_test_steps:
        #step: create an sfs-filesystem with an invalid path
        #result: expected validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc33')
    def obsolete_33_n_create_duplicate_export(self):
        """
        Converted to AT "test_33_n_create_duplicate_export.at" in nas
        #tms_id: litpcds_8524_tc33
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates duplicate sfs-exports
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a duplicate sfs-export
        #result: item created in model
        #step: run create_plan
        #result: expected validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc34')
    def obsolete_34_n_export_requires_allowed_clients(self):
        """
        Converted to AT "test_34_n_export_requires_allowed_clients.at" in
        nasapi
        #tms_id: litpcds_8524_tc34
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that attempts to create sfs-export
            without "ip4allowed_clients" set
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create a sfs-export without "ip4allowed_clients"
        #result: expected error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc35')
    def obsolete_35_n_export_with_invalid_ipv4_range(self):
        """
        Converted to AT "test_35_n_export_with_invalid_ipv4_range.at" in
        nasapi
        #tms_id: litpcds_8524_tc35
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that attempts to create an export with invalid ipv4 range
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export with invalid IP range
        #result: validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc36')
    def obsolete_36_n_create_export_with_invalid_ipv4allowed_clients(self):
        """
        Converted to AT
        "test_36_n_create_export_with_invalid_ipv4allowed_clients.at" in nasapi
        #tms_id: litpcds_8524_tc36
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export's allowed_clients
            with an invalid deliminator
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: expected error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story8524', 'story8524_tc37')
    def obsolete_37_n_export_with_invalid_allowed_clients_not_ipv4s(self):
        """
        Converted to AT
        "test_37_n_export_with_invalid_allowed_clients_not_ipv4s.at" in nasapi
        #tms_id: litpcds_8524_tc37
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export with invalid allowed_clients
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export with invalid allowed_clients
        #result: expected validation given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc38')
    def obsolete_38_n_create_conflicting_exports(self):
        """
        Converted to AT "test_38_n_create_conflicting_exports.at" in nas
        #tms_id: litpcds_8524_tc38
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that attempts to create conflicting exports
            and ensure expected eror generated
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create plan
        #result: expected error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc39')
    def obsolete_39_n_create_export_with_duplicate_allowed_clients(self):
        """
        Converted to AT
        "test_39_n_create_export_with_duplicate_allowed_clients.at" in nasapi
        #tms_id: litpcds_8524_tc39
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export with invalid allowed_clients
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export with duplicate allowed clients
        #result: expected error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc40')
    def obsolete_40_n_export_requires_options(self):
        """
        Converted to AT "test_40_n_export_requires_options.at" in nasapi
        #tms_id: litpcds_8524_tc40
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export without the "options"
            parameter
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export without 'options' property
        #result: expected error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc41')
    def obsolete_41_n_export_invalid_deliminator_options(self):
        """
        Converted to AT "test_41_n_export_invalid_deliminator_options.at" in
        nasapi
        #tms_id: litpcds_8524_tc41
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export with invalid deliminator
            "options"
            parameter
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: expected validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc42')
    def obsolete_42_n_conflicting_export_options(self):
        """
        Converted to AT "test_42_n_conflicting_export_options.at" in nasapi
        #tms_id: litpcds_8524_tc42
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an export with conflicting
            "options" parameter
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export with conflicting options
        #result: expected validation error given
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc43')
    def obsolete_43_n_invalid_mount_provider(self):
        """
        Converted to AT "test_43_n_invalid_mount_provider.at" in nas
        #tms_id: litpcds_8524_tc43
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with the "provider"
            that doesn't match a vip parameter
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create an nfs-mount on node where the "provider" doesn't
        match any vip's "name"
        #result: item created in model
        #step: create plan
        #result: plan creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story8524', 'story8524_tc44')
    def test_44_n_invalid_mount_export_path(self):
        """
        @tms_id: litpcds_8524_tc44
        @tms_requirements_id: LITPCDS-8524
        @tms_title: Create SFS filesystem and shares
        @tms_description:
            Test that creates an nfs-mount with the "export_path"
            that doesn't match any vip path
        @tms_test_steps:
        @step: create an sfs-filesystem
        @result: item created in model
        @step: create an sfs-export
        @result: item created in model
        @step: create an nfs-mount on node
        @result: item created in model
        @step: create plan
        @result: plan creation fails with expected error
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test44"
        path = "/vx/8524-fs1" + test_number
        file_system = "8524-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8524' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8524' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_8524' +\
                    test_number
        nfs_mount_props = "export_path=" "'" "/vx/blabla" "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_8524' + \
                           test_number

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
        # 3. create an nfs-mount on node
        self.create_item(item_path=nfs_mount,
                         item_type="nfs-mount",
                         item_props=nfs_mount_props,
                         xml_path=self.nfs_mount_xml)
        # 4. inherit mount to node
        self.inherit(path=node_file_system, source_path=nfs_mount)
        try:
            # 5. create plan and ensure it fails with correct error
            self.create_plan(plan_outcome=test_constants.PLAN_FAILED)
            # 6. Ensure the state of the model item is "Initial"
            self.assertTrue(
                "Initial (deployment of properties indeterminable)" in
                self.get_item_state(self.ms_node, node_file_system))
        finally:
            # 7. clean the sfs
            self.clean_sfs(file_system=file_system,
                           path=path)

    # attr('all', 'revert', 'story8524', 'story8524_tc45')
    def obsolete_45_n_create_export_with_invalid_allowed_ip(self):
        """
        Converted to AT "test_45_n_create_export_with_invalid_allowed_ip.at"
        in nas
        #tms_id: litpcds_8524_tc45
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount on a invalid ip
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create an nfs-mount on node
        #result: item created in model
        #step: create plan
        #result: plan creation should fail with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc46')
    def obsolete_46_n_invalid_mount_mount_options(self):
        """
        Converted to AT "test_46_n_invalid_mount_mount_options.at" in nasapi
        #tms_id: litpcds_8524_tc46
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with an invalid option delimiter
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with mount_options separated by a delimiter
        other than a comma
        #result: creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
            creation of item should fail
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc47')
    def obsolete_47_n_duplicate_mount_mount_options(self):
        """
        Converted to AT "test_47_n_duplicate_mount_mount_options.at" in nasapi
        #tms_id: litpcds_8524_tc47
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with duplicate options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with mount_options with duplicate
        mount_options
        #result: item creation fails with expected error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc48')
    def obsolete_48_n_conflicting_mount_mount_options(self):
        """
        Converted to AT "test_48_n_conflicting_mount_mount_options.at" in
        nasapi
        #tms_id: litpcds_8524_tc48
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with conflicting options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with mount_options with conflicting
        mount options
        #result: creation should fail
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc49')
    def obsolete_49_n_invalid_mount_options_value(self):
        """
        Converted to AT "test_49_n_invalid_mount_options_value.at" in nasapi
        #tms_id: litpcds_8524_tc49
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc50')
    def obsolete_50_n_invalid_sec_mount_option(self):
        """
        Converted to AT "test_50_n_invalid_sec_mount_option.at" in nasapi
        #tms_id: litpcds_8524_tc50
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc51')
    def obsolete_51_n_invalid_proto_mount_option(self):
        """
        Converted to AT "test_51_n_invalid_proto_mount_option.at" in nasapi
        #tms_id: litpcds_8524_tc51
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid proto mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc52')
    def obsolete_52_n_invalid_lookupcache_mount_option(self):
        """
        Converted to AT "test_52_n_invalid_lookupcache_mount_option.at" in
        nasapi
        #tms_id: litpcds_8524_tc52
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid lookupcache mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc53')
    def obsolete_53_n_invalid_clientaddr_mount_option(self):
        """
        Converted to AT "test_53_n_invalid_clientaddr_mount_option.at" in
        nasapi
        #tms_id: litpcds_8524_tc53
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
        #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid clientaddr mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8524', 'story8524_tc54')
    def obsolete_54_n_invalid_timeo_mount_option(self):
        """
        Converted to AT "test_54_n_invalid_timeo_mount_option.at" in nasapi
        #tms_id: litpcds_8524_tc54
        #tms_requirements_id: LITPCDS-8524
        #tms_title: Create SFS filesystem and shares
               #tms_description:
            Test that creates an nfs-mount with invalid options
        #tms_test_steps:
        #step: create an sfs-filesystem
        #result: item created in model
        #step: create an sfs-export
        #result: item created in model
        #step: create a nfs-mount with invalid timeo mount_options
        #result: expected validation error generated
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
