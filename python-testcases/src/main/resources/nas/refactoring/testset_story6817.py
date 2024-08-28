"""
@copyright: Ericsson Ltd
@since:     June 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-6817
"""
from litp_generic_test import GenericTest, attr
import test_constants
from xml_utils import XMLUtils


class Story6817(GenericTest):
    """
    LITPCDS-6817:
        As a LITP user, I want to grow existing NAS file systems,
        so I can meet growing application requirments regards disk space.
    """

    def setUp(self):
        """Run before every test"""
        super(Story6817, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story6817, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story6817.xml"):
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

    def clean_sfs(self, file_systems, cache_name=None, snaps=()):
        """
        Method that cleans the sfs to it's previous state
        """
        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
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
                    self.assertTrue(self.is_sfs_snapshot_present(
                        self.nas_server, snapshot_name=snap))
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

    def change_fs_size_on_sfs(self, fs_name, node=None, increase=True,
                              tier="primary", size=None, pool="litp2"):
        """
        Method that increases or decreases the size of a filesystem
        directly on the sfs
        """
        node = node or self.nas_server
        if increase:
            self.assertTrue(self.increase_sfs_size(
                sfs_node=node, tier=tier, fs_test=fs_name,
                size=size, pool_name=pool))

        else:
            self.assertTrue(self.decrease_sfs_size(
                sfs_node=node, tier=tier, fs_test=fs_name, size=size))

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc01')
    def test_01_p_expand_multiple_filesystems(self):
        """
        #tms_id: litpcds_6817_tc01
        #tms_requirements_id: LITPCDS-6817
        #tms_title: expand multiple filesystems
        #tms_description: Test that ensures we can expand multiple
        sfs-filesystems
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 0
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update size=20g property of both sfs-filesystem items
        #result: item updated
        #step: Create and run plan
        #result: plan executes successfully
        #result: filesystems are the correct size on the sfs
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test01"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "0" "' "
        sfs_filesystem_props3 = "size=20G"

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
            # 6. Increase the size of both filesystems to 20G
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3)
            # 7. Create and run the plan
            self.create_plan()
            # 8. Ensure the filesystems are the correct size on the sfs
            self.check_sfs(file_systems, fs_size="20.00G")

        finally:
            self.clean_sfs(file_systems)

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc02')
    def test_02_n_expand_filesystem_size_and_snapshot(self):
        """
        #tms_id: litpcds_6817_tc02
        #tms_requirements_id: LITPCDS-6817
        #tms_title: expand filesystem size and snapshot
        #tms_description:  Test that ensures we can't take a snapshot if
        there are updated filesystems in the model
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update size=20G property of both sfs-filesystem items
        #result: item updated
        #step: Create snapshot
        #result: error thrown: ValidationError
        #result: message shown: Create snapshot failed: A snapshot may not
        be created while an sfs-filesystem "size" property update is pending.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test02"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "size=20G"
        error_message = 'Create snapshot failed: A snapshot may not ' \
                        'be created while an sfs-filesystem "size" ' \
                        'property update is pending.'

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
            # 6. Increase the size of both filesystems to 20G
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3)
            # 7. Create a snapshot
            self.create_snapshot(expect_positive=False,
                                 error_message=error_message)

        finally:
            self.clean_sfs(file_systems)

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc03')
    def test_03_p_manually_change_fs_size_on_sfs(self):
        """
        #tms_id: litpcds_6817_tc03
        #tms_requirements_id: LITPCDS-6817
        #tms_title: manually change fs size on sfs
        #tms_description: Test that ensures we can manually change the size
            of a file system on the sfs and update the model to the same or
            greater size
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: Manually decrease the first file system to 5G on the sfs
        #result: item updated
        #step: Manually increase the second file system to 20G on the sfs
        #result: item updated
        #step: Update both file systems in the model to 20G
        #result: Items updates successfully
        #step: Create and run plan
        #result: Plan is successful
        #step: Ensure both file systems are 20G on the sfs
        #result: File systems are the correct size on the sfs
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test03"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "size=20G"

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
            # 6. manually decrease fs1 to 5G on the sfs
            self.change_fs_size_on_sfs(fs_name=file_system,
                                       increase=False, size="5G")
            # 7. manually increase fs2 to 20G on the sfs
            self.change_fs_size_on_sfs(fs_name=file_system2, size="20G")
            # 8. Increase the size of both filesystems to 20G
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3)
            # 9. Create and run the plan
            self.create_plan()
            # 10. ensure filesystems are the correct size on the sfs
            self.check_sfs(file_systems, fs_size="20.00G")

        finally:
            self.clean_sfs(file_systems)

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc04')
    def test_04_n_manually_increase_fs_size_on_sfs_to_larger_size(self):
        """
        #tms_id: litpcds_6817_tc04
        #tms_requirements_id: LITPCDS-6817
        #tms_title: manually increase fs size on sfs to larger size
        #tms_description: Test that manually increases the size of a
        filesystems directly on the sfs and then in the model
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: manually increase fs2 to 30G on the sfs
        #result: sfs increased
        #step: update size=20G property of second sfs-filesystem item
        #result: item updated
        #step: Create and run plan
        #result: run plan fails
        #result: message in  /var/logs: Shrinking the existing file system
        is not supported.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test04"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "size=20G"
        expected_error_logs = ['Shrinking the existing file system '
                               'is not supported.']

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
            # 6. manually increase fs2 to 30G on the sfs
            self.change_fs_size_on_sfs(fs_name=file_system2, size="30G")
            # 7. Increase the size of the filesystem to 20G
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3)
            # 8. Create and run plan
            self.create_plan(plan_outcome=test_constants.PLAN_FAILED)

            # 9. check /var/log/messages for correct error
            self.grep_logs(message=expected_error_logs)

        finally:
            self.clean_sfs(file_systems)

    #@attr('all', 'revert', 'story6817', 'story6817_tc05')
    def obsolete_05_n_reduce_sfs_filesystem_size(self):
        """
        Converted to AT "test_05_n_reduce_sfs_filesystem_size.at" in nas
        #tms_id: litpcds_6817_tc05
        #tms_requirements_id: LITPCDS-6817
        #tms_title: reduce sfs filesystem size
        #tms_description: Test that tries to reduce the size of an
        sfs-filesystem
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update size=5G property of first sfs-filesystem item
        #result: item updated
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: Decreasing the value "10G" of property "size"
        of an sfs-filesystem is not supported
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc06')
    def test_06_n_increase_fs_size_too_large(self):
        """
        #tms_id: litpcds_6817_tc06
        #tms_requirements_id: LITPCDS-6817
        #tms_title: increase fs size too large
        #tms_description: Test that updates the size of a filesystem to a
        size larger than the space available on the sfs
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update size=9T property of second sfs-filesystem item
        #result: item updated
        #step: Create  and run plan plan
        #result: run plan fails
        #result: message in  /var/logs: NAS fs ERROR V-288-2128 Unable to
        allocate space to grow fs 6817-fs1_test06_b due to either insufficient
        space
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test06"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "size=9T"
        expected_error_logs = ['fs ERROR V-288-2128 Unable to allocate '
                               'space to grow fs 6817-fs1_test06_b due to '
                               'either insufficient space']

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
            # 5. Ensure filesystems was created
            self.check_sfs(file_systems)
            # 6. Increase the size of the filesystem to 9G
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3)
            # 7. Create and run plan
            self.create_plan(plan_outcome=test_constants.PLAN_FAILED)
            # 8. check /var/log/messages for correct error
            self.grep_logs(message=expected_error_logs)

        finally:
            self.clean_sfs(file_systems)

    @attr('pre-reg', 'revert', 'story6817', 'story6817_tc07')
    def test_07_n_invalid_update_to_filesystem_size(self):
        """
        #tms_id: litpcds_6817_tc07
        #tms_requirements_id: LITPCDS-6817
        #tms_title: invalid update to filesystem size
        #tms_description: Test that updates the size of a filesystem to an
        invalid value
        #tms_test_steps:
        #step: Create sfs-cache item  under "/infrastructure"
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G
        #result: items created
        #step: Create sfs-filesystem item  under "/infrastructure"
        size of 10G and snap_size of 10
        #result: items created
        #step: Create and run plan
        #result: plan executes successfully
        #step: update size=f property of second sfs-filesystem item
        #result: error thrown: ValidationError
        #result: message shown: Invalid value 'f'
        #step: update size=10K property of second sfs-filesystem item
        #result: error thrown: ValidationError
        #result: message shown: Invalid value '10K'
        #step: update size=1_M property of second sfs-filesystem item
        #result: error thrown: ValidationError
        #result: message shown: Invalid value '1_M'
        #step: update size=10m property of second sfs-filesystem item
        #result: error thrown: ValidationError
        #result: message shown: Invalid value '10m'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test07"
        file_system = "6817-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "6817-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "6817_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_6817' \
                          + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "size=f"
        sfs_filesystem_props4 = "size=10K"
        sfs_filesystem_props5 = "size=1_M"
        sfs_filesystem_props6 = "size=10m"
        error_message1 = "Invalid value 'f'."
        error_message2 = "Invalid value '10K'."
        error_message3 = "Invalid value '1_M'."
        error_message4 = "Invalid value '10m'."

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
            # 5. Ensure filesystems was created
            self.check_sfs(file_systems)
            # 6. Update the size of the second filesystem to an invalid value
            self.update_item(expect_positive=False,
                             item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props3,
                             error_type="ValidationError",
                             error_message=error_message1)
            self.update_item(expect_positive=False,
                             item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props4,
                             error_type="ValidationError",
                             error_message=error_message2)
            self.update_item(expect_positive=False,
                             item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props5,
                             error_type="ValidationError",
                             error_message=error_message3)
            self.update_item(expect_positive=False,
                             item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props6,
                             error_type="ValidationError",
                             error_message=error_message4)

        finally:
            self.clean_sfs(file_systems)
