"""
@copyright: Ericsson Ltd
@since:     March 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-8062
"""
from litp_generic_test import GenericTest, attr
from storage_utils import StorageUtils
import test_constants
from xml_utils import XMLUtils


class Story8062(GenericTest):
    """
    LITPCDS-8062:
        As a LITP installer I want to be able to specify a subnet from
        which access to an NAS export is allowed so that my
        installation time is reduced
    """

    def setUp(self):
        """Run before every test"""
        super(Story8062, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.storage = StorageUtils()
        self.xml = XMLUtils()
        self.node1_ip_address = self.get_node_att(self.mn_nodes[0], 'ipv4')

        self.nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        self.nfsmount_url = self.find(self.ms_node, "/infrastructure",
                                      "storage", True)
        self.nfs_mount_xml = self.nfsmount_url[0] + '/nfs_mounts'
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")

    def tearDown(self):
        """Run after every test"""
        super(Story8062, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story8062.xml"):
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

    def grep_logs(self, message, node=None,
                  log=test_constants.GEN_SYSTEM_LOG_PATH, grep_args=''):
        """
        Method to grep logs for given error message
        """
        node = node or self.ms_node
        stdout = self.run_command(
            node, self.rhc.get_grep_file_cmd(
                log, message, grep_args=grep_args),
            su_root=True, default_asserts=True)[0]

        self.assertNotEqual([], stdout)

    @attr('all', 'revert', 'story8062', 'story8062_tc01')
    def test_01_p_create_share_with_subnets(self):
        """
        @tms_id: litpcds_8062_tc01
        @tms_requirements_id: LITPCDS-8062
        @tms_title: create share with subnets
        @tms_description: Test that creates an export with 2 subnets as
        allowed clients
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with two
        values in ipv4allowed_clients property
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @result: shares are created
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test01"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + \
                           "'192.167.0.0/16,192.168.0.0/16' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

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
            self.check_sfs(file_system, path, ip_add="192.167.0.0/16")
            self.check_sfs(file_system, path, ip_add="192.168.0.0/16")

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8062', 'story8062_tc02')
    def test_02_p_share_with_ip_and_subnet(self):
        """
        @tms_id: litpcds_8062_tc02
        @tms_requirements_id: LITPCDS-8062
        @tms_title: create share with ip and subnets
        @tms_description: Test that creates an export with one subnet and one
        ip as allowed clients
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with two
        values in ipv4allowed_clients property, one ip and one subnet
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test02"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + \
                           "'192.167.0.0/16,44.54.23.53' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

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
            self.check_sfs(file_system, path, ip_add="192.167.0.0/16")
            self.check_sfs(file_system, path, ip_add="44.54.23.53")

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8062', 'story8062_tc03')
    def test_03_p_create_share_with_subnets_and_ips(self):
        """
        @tms_id: litpcds_8062_tc03
        @tms_requirements_id: LITPCDS-8062
        @tms_title: create share with subnets and ips
        @tms_description: Test that creates an export with 2 subnets and 2 ips
        as allowed clients
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with four
        values in ipv4allowed_clients property, two ips and two subnets
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test03"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + \
                           "'192.167.0.0/16,192.168.0.0/16," \
                           "44.44.44.44,45.45.45.45' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

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
            self.check_sfs(file_system, path, ip_add="192.167.0.0/16")
            self.check_sfs(file_system, path, ip_add="192.168.0.0/16")
            self.check_sfs(file_system, path, ip_add="44.44.44.44")
            self.check_sfs(file_system, path, ip_add="45.45.45.45")

        finally:
            self.clean_sfs(file_system, path)

    # attr('all', 'revert', 'story8062', 'story8062_tc04')
    def obsolete_04_n_create_invalid_subnet(self):
        """
        Converted to AT "test_04_n_create_invalid_subnet.at" in nasapi
        #tms_id: litpcds_8062_tc04
        #tms_requirements_id: LITPCDS-8062
        #tms_title: create_invalid_subnet
        #tms_description: Test that creates an export with an invalid subnet
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item under "/infrastructure" with invalid
        subnet value in ipv4allowed_clients property
        #result: error thrown: ValidationError
        #result: message shown: only accepts a list of valid IPv4
        address(es)/subnet(s) separated by single commas
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story8062', 'story8062_tc05')
    def test_05_p_add_subnet_to_export(self):
        """
        @tms_id: litpcds_8062_tc05
        @tms_requirements_id: LITPCDS-8062
        @tms_title: add_subnet to export
        @tms_description: Test that ensures we can add a subnet allowed_client
        to an existing export
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with one
        subnet value in ipv4allowed_clients property
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update sfs-export item under "/infrastructure" with another
        subnet value in ipv4allowed_clients property
        @result: item updated
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test05"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + \
                           "'192.167.0.0/16' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                            "192.167.0.0/16,192.168.0.0/16" + "'"

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
            self.check_sfs(file_system, path, ip_add="192.167.0.0/16")
            # 5. Update the export with another ip
            self.update_item(sfs_export, item_props=sfs_export_props2)
            # 6. create and run plan
            self.create_plan()
            # 7. ensure the new share is created
            self.check_sfs(file_system, path, ip_add="192.168.0.0/16")

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8062', 'story8062_tc06')
    def test_06_p_remove_subnet_from_export(self):
        """
        @tms_id: litpcds_8062_tc06
        @tms_requirements_id: LITPCDS-8062
        @tms_title: remove subnet to export
        @tms_description: Test that ensures we can remove a subnet
        allowed_client to an existing export
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with two
        subnet value in ipv4allowed_clients property
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @step: update sfs-export item under "/infrastructure" remove
        subnet value in ipv4allowed_clients property
        @result: item updated
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test06"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + \
                           "'192.167.0.0/16,192.168.0.0/16' " + \
                           "options=" + "'" "rw,no_root_squash" "' "
        sfs_export_props2 = "ipv4allowed_clients=" + "'" + \
                            "192.167.0.0/16" + "'"

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
            self.check_sfs(file_system, path, ip_add="192.167.0.0/16")
            self.check_sfs(file_system, path, ip_add="192.168.0.0/16")
            # 5. Update the export with another ip
            self.update_item(sfs_export, item_props=sfs_export_props2)
            # 6. create and run plan
            self.create_plan()
            # 7. ensure the new share is created
            self.check_sfs(file_system, path, share_present=False,
                           ip_add="192.168.0.0/16")

        finally:
            self.clean_sfs(file_system, path)

    @attr('all', 'revert', 'story8062', 'story8062_tc07')
    def test_07_p_create_export_that_exists_on_sfs_with_subnet(self):
        """
        @tms_id: litpcds_8062_tc07
        @tms_requirements_id: LITPCDS-8062
        @tms_title: create export that exists on sfs with subnet
        @tms_description:Test that creates a filesystem and export that already
        exist on the sfs with a subnet
        @tms_test_steps:
        @step: Create sfs-filesystem and share manually
        @result: sfs-filesystem and share created manually
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure"
        @result: item created
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test07"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           "192.168.0.0/16" + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

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
                                  share_ipaddrs="192.168.0.0/16"))
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 3. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml)
        try:
            # 4. Create and run the plan
            self.create_plan()
            # 5. Ensure share was created
            self.check_sfs(file_system, path, ip_add="192.168.0.0/16")
        finally:
            self.clean_sfs(file_system=file_system, path=path)

    @attr('all', 'revert', 'story8062', 'story8062_tc08')
    def test_08_n_export_that_exists_on_sfs_with_different_options(self):
        """
        @tms_id: litpcds_8062_tc08
        @tms_requirements_id: LITPCDS-8062
        @tms_title: create export that exists on sfs with subnet
        @tms_description: Test that creates a filesystem and export that
        already exist on the sfs with a subnet but with different options
        @tms_test_steps:
        @step: Create sfs-filesystem and share manually
        @result: sfs-filesystem and share created manually
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with different
        options
        @result: item created
        @step: Create and run plan
        @result: plan fails
        @result: error in var/log/messages: already exists in NAS but it's
        options do not match
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test08"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           "192.168.0.0/16" + "' " + \
                           "options=" + "'" "ro,no_root_squash" "' "

        # There are two alternative log messages to search for, as with VA 7.4
        # the message differed slightly. This message now accounts for SFS,
        # VA 7.2 and VA 7.4
        expected_error_logs = ['The file system \\"' + file_system
                               + '\\" already exists on NAS|already exists '
                                 'in NAS but it\'s options do not match']
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
                                  share_ipaddrs="192.168.0.0/16"))
        # 2. create an sfs-filesystem
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        # 3. create an sfs-export
        self.create_item(item_path=sfs_export,
                         item_type="sfs-export",
                         item_props=sfs_export_props,
                         xml_path=sfs_export_xml)
        try:
            # 4. Create and run the plan
            self.create_plan(plan_outcome=test_constants.PLAN_FAILED)

            # 5. check /var/log/messages for correct error
            self.grep_logs(message=expected_error_logs, grep_args='-E')

        finally:
            self.clean_sfs(file_system=file_system, path=path)

    @attr('all', 'revert', 'story8062', 'story8062_tc09')
    def test_09_p_mount_shares_from_exported_subnet(self):
        """
        @tms_id: litpcds_8062_tc09
        @tms_requirements_id: LITPCDS-8062
        @tms_title: Test that creates an export and a mount
        @tms_description: Test that creates an export and a mount
        @tms_test_steps:
        @step: Create sfs-filesystem item  under "/infrastructure"
        @result: items created
        @step: Create sfs-export item under "/infrastructure" with different
        options
        @result: item created
        @step: Create nfs-mount item  under "/infrastructure" and inherits
        onto node 1
        @result: items created
        @step: Create and run plan
        @result: plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "_test09"
        path = "/vx/8062-fs1" + test_number
        file_system = "8062-fs1" + test_number
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_8062' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "'"
        sfs_export = sfs_filesystem + '/exports/ex1_8062' + test_number
        sfs_export_xml = sfs_filesystem + '/exports'
        nfs_mount = self.nfsmount_url[0] + '/nfs_mounts/nm1_8062' + test_number
        nfs_mount_props = "export_path=" "'" + path + "' " + \
                          "network_name=" "'" "mgmt" "' " + \
                          "provider=" "'" "virtserv1" "' " + \
                          "mount_options=" "'" "soft" "' " + \
                          "mount_point=" + "'" + "/test1" + "'"
        node_file_system = self.nodes_url[0] + '/file_systems/nm1_8062' + \
                           test_number

        sfs_export_props = "ipv4allowed_clients=" + "'" + \
                           "192.168.0.0/16" + "' " + \
                           "options=" + "'" "rw,no_root_squash" "' "

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
            self.check_sfs(file_system=file_system, path=path,
                           ip_add="192.168.0.0/16")
            # 6. check for mount in fstab
            self.check_mount_in_fstab(file_system, path,
                                      self.mn_nodes[0])
        finally:
            self.clean_sfs(file_system=file_system,
                           path=path)

    # attr('all', 'revert', 'story8062', 'story8062_tc10')
    def obsolete_10_n_share_with_subnet_and_ip_within_subnet(self):
        """
        Converted to AT "test_10_n_share_with_subnet_and_ip_within_subnet.at"
        in nasapi
        #tms_id: litpcds_8062_tc10
        #tms_requirements_id: LITPCDS-8062
        #tms_title: Test that creates an export and a mount
        #tms_description: Test that creates an export with a subnet and an ip
        within the subnet
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item under "/infrastructure" with a subnet
        and ip within the subnet
        #result:error thrown: ValidationError
        #result: message shown: IP address overlaps with subnet
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story8062', 'story8062_tc11')
    def obsolete_11_n_shares_with_conflicing_ip_and_subnet(self):
        """
        Converted to AT "test_11_n_shares_with_conflicing_ip_and_subnet.at"
        in nas
        #tms_id: litpcds_8062_tc11
        #tms_requirements_id: LITPCDS-8062
        #tms_title: shares with conflicting ip and subnet
        #tms_description: Test that creates two exports with conflicting
        allowed clients
        #tms_test_steps:
        #step: Create sfs-filesystem item  under "/infrastructure"
        #result: items created
        #step: Create sfs-export item under "/infrastructure" with a subnet
        #result: item created
        #step: Create another sfs-export item under "/infrastructure" with a ip
        within the previous items subnet
        #result: item created
        #step: create plan
        #result:error thrown: ValidationError
        #result: message shown: Create plan failed: IP address
        is already defined or overlaps with subnet
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
