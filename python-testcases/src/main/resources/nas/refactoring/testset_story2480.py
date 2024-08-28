"""
@copyright: Ericsson Ltd
@since:     April 2015
@author:    etomgly
@summary:   Tests for NAS plugin stories:
            LITPCDS-2480
"""
from litp_generic_test import GenericTest, attr
import test_constants
from xml_utils import XMLUtils


class Story2480(GenericTest):
    """
    LITPCDS-2480:
        As a LITP User I want to create an SFS snapshot.
    """

    def setUp(self):
        """Run before every test"""
        super(Story2480, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Story2480, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_story2480.xml"):
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

        sfs_del = True
        for filesystem in file_systems:
            self.assertTrue(self.delete_sfs_fs(self.nas_server, filesystem))
        self.assertTrue(sfs_del)

        if cache_name is not None:
            self.assertTrue(self.delete_sfs_cache(self.nas_server,
                                                  cache_name))

    def check_sfs(self, file_systems, snaps=(), snap_present=True,
                  cache_present=True, cache_name=None, cache_size=None):
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
                    self.nas_server, filesystem))

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

    def snapshot_item_exists(self, name=None, base_snapshot=True):
        """
        Description:
            Determine if a snapshot item exists in the model.
        Results:
            Boolean, True if exists or False otherwise
         """
        snapshot_url = self.find(self.ms_node, "/snapshots",
                              "snapshot-base", assert_not_empty=False)
        if base_snapshot:
            for snap in snapshot_url:
                if snap == "/snapshots/snapshot":
                    return True
                else:
                    return False

        else:
            if name:
                for snap in snapshot_url:
                    if snap == "/snapshots/" + name:
                        return True
                    else:
                        return False
            else:
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

    def delete_snapshot(self, name=None):
        """
        Delete the snapshots
        """

        if name is not None:
            args = "-n " + name
            if self.snapshot_item_exists(base_snapshot=False, name=name):
                self.execute_cli_removesnapshot_cmd(self.ms_node, args=args)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, self.timeout_mins))
        else:
            args = ''
            if self.snapshot_item_exists():
                self.execute_cli_removesnapshot_cmd(self.ms_node, args=args)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, self.timeout_mins))

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

    def check_plan_output(self, message, should_be_present=False):
        """
        greps show_plan
        """
        # 1. Run show_plan
        stdout, _, _ = self.execute_cli_showplan_cmd(self.ms_node)
        # 2. Verify that there are no snapshot tasks in the plan.
        if not should_be_present:
            self.assertFalse(self.is_text_in_list(message, stdout))

        else:
            self.assertTrue(self.is_text_in_list(message, stdout))

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

    #@attr('all', 'revert', 'story2480', 'story2480_tc01')
    def obsolete_01_p_create_snapshot_of_multiple_filesystems(self):
        """
        Merged with test 03
        #tms_id: litpcds_2480_tc01
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Create snapshot of multiple filesystems
        #tms_description: Test to ensure that a snapshot can be created
        #tms_test_steps:
            #step: Create an sfs-cache under infrastructure
            #result: sfs-cache created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Ensure filesystems were created
            #result: Filesystems are present
            #step: Create snapshot
            #result: Create snapshot should be successful
            #step: Check the cache and snap were created
            #result: Snapshot and cache are present and in correct state
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc02')
    def test_02_p_create_and_delete_snapshot_with_name(self):
        """
        Now covers litpcds_3612_tc02
        #tms_id: litpcds_2480_tc02
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Create named snapshot
        #tms_description: Test to ensure that a named snapshot can be created
            and deleted
        #tms_test_steps:
            #step: Create an sfs-cache under infrastructure
            #result: sfs-cache created
            #step: Create two sfs-filesystems
            #result: sfs-filesystems created
            #step: Create and run the plan
            #result: Plan is successful
            #step: Create snapshot with name
            #result: snapshot created
            #step: Check that the filesystems, snapshot and cache are present
            #result: Filesystems, snapshot and cache are present
            in the correct state
            #step: Remove named snapshot
            #result: Snapshot removed successfully
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test02"
        file_systems = []
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "2480-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "2480_cache" + test_number
        snap = "2480-2"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = \
            "path='{0}' size='10G' cache_name='{1}' snap_size='10'".format(
                path, cache_name)
        sfs_filesystem_props2 = \
            "path='{0}' size='20G' cache_name='{1}' snap_size='10'".format(
                path2, cache_name)

        self.log('info', "1. Create an sfs-cache")
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)

        self.log('info', "2. Create two sfs-filesystems")
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)

        try:
            self.log('info', "3. Create and run plan")
            self.create_plan()
            self.check_sfs(file_systems)

            self.log('info', "4. Create snapshot")
            self.create_snapshot(name=snap)
            snaps.append(snap)

            self.log('info', "5. Check the sfs for the filesystems snapshot "
                "and cache")
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="3072", snaps=snaps)

            self.log('info', "6. Delete snapshot")
            self.delete_snapshot(name=snap)

            self.log('info', "7. Ensure the snapshot was removed from the sfs")
            self.check_sfs(file_systems, snaps=snaps, snap_present=False,
                           cache_name=cache_name, cache_present=False)

        finally:
            self.log('info', "8. Cleanup after test")
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc03')
    def test_03_p_verify_sfs_cache(self):
        """
        Now covers litpcds_2480_tc01, litpcds_2480_tc04, litpcds_2480_tc05,
        litpcds_3612_tc01 and litpcds_3612_tc03
        #tms_id: litpcds_2480_tc03
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Performs multiple operations to validate sfs cache
        #tms_description: Test that ensures when we create a cache manually
        a plan creating the cache succeeds, adding filesystems and creating
        a snapshot increases the cache object in size and updating a
        filesystem and creating a snapshot increases cache size
        #tms_test_steps:
            #step: Create an sfs-cache manually on the sfs
            #result: sfs-cache created successfully
            #step: Create an sfs-cache under infrastructure
            #result: sfs-cache created
            #step: Create two sfs-filesystems
            #result: sfs-filesystems created
            #step: Create and run the plan
            #result: Plan is successful
            #step: Create snapshot
            #result: Snapshot created
            #step: Check the filesystems, snapshot and cache
            #result: All items are present in the correct state
            #step: Create another sfs-filesystem
            #result: sfs-filesystem is created
            #step: Remove old snapshot
            #result: Snapshot removed
            #step: Create another snapshot
            #result: snapshot is created
            #step: Check the filesystem, cache and snapshot items
            #result: All items are in the correct state, and the cache size
                     has increased.
            #step: Update snapsize of a filesystem
            #result: Snapsize updated
            #step: Remove old snapshot manually
            #result: Snapshot removed
            #step: Run remove snapshot
            #result: Plan is successful
            #step: Create a new snapshot
            #result: New snapshot created and cache size has increased
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test03"
        file_systems = []

        file_system = "2480-fs1" + test_number
        path = "/vx/" + file_system

        file_system2 = "2480-fs1" + test_number + "_b"
        path2 = "/vx/" + file_system2

        file_system3 = "2480-fs1" + test_number + "_c"
        path3 = "/vx/" + file_system3

        file_systems.append(file_system)
        file_systems.append(file_system2)
        # file_system3 will be appended later

        cache_name = "2480_cache" + test_number
        snap = "2480-3"
        snap2 = "2480-3b"
        snap3 = "2480-3c"
        snaps = []

        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_b"
        sfs_filesystem3 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_c"

        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = \
            "path='{0}' size='10G' cache_name='{1}' snap_size='10'".format(
                path, cache_name)
        sfs_filesystem_props2 = \
            "path='{0}' size='20G' cache_name='{1}' snap_size='10'".format(
                path2, cache_name)
        sfs_filesystem_props3 = \
            "path='{0}' size='10G' cache_name='{1}' snap_size='10'".format(
                path3, cache_name)
        updated_props_3 = "snap_size=" + "'" "20" "' "
        snapshot_name = "L_" + file_system + "_" + snap2
        snapshot_name2 = "L_" + file_system2 + "_" + snap2
        snapshot_name3 = "L_" + file_system3 + "_" + snap2

        self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
        self.log('info', "1. Create an sfs-cache manually on the sfs")
        self.assertTrue(self.create_sfs_cache(self.nas_server,
                                             cache_name=cache_name,
                                             cache_size="1G",
                                             cache_pool="litp2"))

        self.log('info', "2. Create an sfs-cache")
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)

        self.log('info', "3. Create sfs-filesystems")
        self.create_item(item_path=sfs_filesystem,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)

        try:
            self.log('info', "4. Create and run plan")
            self.create_plan()

            self.log('info', "5. Create a snapshot")
            self.create_snapshot(name=snap)
            snaps.append(snap)

            self.log('info', "6. Check the sfs for the filesystems, "
                "snapshot and cache")
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="3072", snaps=snaps)

            self.log('info', "7. Create another sfs-filesystem")
            self.create_item(item_path=sfs_filesystem3,
                             item_type="sfs-filesystem",
                             item_props=sfs_filesystem_props3,
                             xml_path=sfs_filesystem_xml)

            self.log('info', "8. Create and run plan")
            self.create_plan()

            self.log('info', "9. Remove old snapshot")
            file_systems.append(file_system3)
            self.delete_snapshot(name=snap)

            self.log('info', "10. Ensure snapshot is removed")
            self.check_sfs(file_systems, snaps=" ", snap_present=False,
                           cache_name=cache_name, cache_present=False)

            self.log('info', "11. Create new snapshot")
            snaps.remove(snap)
            self.create_snapshot(name=snap2)
            snaps.append(snap2)

            self.log('info', "12. Assert cache size increased by "
                "the correct amount")
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="4096", snaps=snaps)

            self.log('info', "13. Update the filesystem snap size")
            self.update_item(item_path=sfs_filesystem3,
                             item_props=updated_props_3)

            self.set_node_connection_data(
                self.nas_server, username=test_constants.SFS_MASTER_USR,
                password=test_constants.SFS_MASTER_PW)

            self.log('info', "14. Remove the snapshot manually")
            self.assertTrue(self.delete_sfs_snapshot(
                self.nas_server, snapshot_test=snapshot_name,
                fs_test=file_system))

            self.assertTrue(self.delete_sfs_snapshot(
                self.nas_server, snapshot_test=snapshot_name2,
                fs_test=file_system2))

            self.assertTrue(self.delete_sfs_snapshot(
                self.nas_server, snapshot_test=snapshot_name3,
                fs_test=file_system3))

            self.log('info', "15. Ensure the snapshot was removed from "
                "the sfs")
            self.check_sfs(file_systems, snaps=snaps, snap_present=False,
                           cache_name=cache_name)

            self.log('info', "16. Run remove_snapshot")
            self.delete_snapshot(name=snap2)

            self.log('info', "17. Ensure the cache is removed")
            self.check_sfs(file_systems, snaps=snaps, snap_present=False,
                           cache_name=cache_name, cache_present=False)

            self.log('info', "18. Create a new snapshot")
            snaps.remove(snap2)
            self.create_snapshot(name=snap3)
            snaps.append(snap3)

            self.log('info', "19. Assert cache size increased by "
                "the correct amount")
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="5120", snaps=snaps)

        finally:
            self.log('info', "20. Cleanup after test")
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    #@attr('all', 'revert', 'story2480', 'story2480_tc04')
    def obsolete_04_p_change_of_snap_size_increases_cache_size(self):
        """
        Merged with test03
        #tms_id: litpcds_2480_tc04
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Change of snap size increases cache size
        #tms_description: Test that ensures when we update a filesystem's
        snap_size and create a snapshot, the cache object is increased in size
        #tms_test_steps:
            #step: Create an sfs-cache under infrastructure
            #result: sfs-cache created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Create snapshot
            #result: snapshot created
            #step: Check that the filesystems, snapshot and cache were created
            #result: Filesystems, snapshot and cache are present in the correct
            state
            #result: Cache will be the correct size; cache_size="1024"
            #step: Update the sfs-filesystem's snap_size
            #result: sfs-filesystem's snap_size is updated
            #step: Create another snapshot
            #result: snapshot is created
            #step: Check that the filesystem and cache are in the correct state
            #result: Cache will be the correct size; cache_size="2048"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc05')
    def obsolete_05_p_create_cache_that_exists(self):
        """
        Merged with test03
        #tms_id: litpcds_2480_tc05
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Create cache that exists
        #tms_description: Test that ensures the manual creation of a cache on
        the sfs
        #tms_test_steps:
            #step: Create an sfs-cache manually on the sfs
            #result: sfs-cache created
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Create snapshot
            #result: Create snapshot is successful
            #step: Check that the filesystems, snapshot and cache were
            created
            #result: Filesystems, snapshot and cache are present
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc06')
    def test_06_p_filesystem_with_snap_size_0(self):
        """
        #tms_id: litpcds_2480_tc06
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Filesystem with snap_size 0
        #tms_description: Test to create a snapshot without sfs
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache created
            #step: Create an sfs-filesystem with a valid cache_name and
            snap_size = 0
            #result: sfs-filesystem created with correct properties
            #step: Create and run the plan
            #result: Plan is running
            #step: Create snapshot
            #result: Snapshot created
            #step: Check the sfs for the snapshot, filesystem and cache
            #result: Expect that none of the above exist in the sfs
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test06"
        file_systems = []
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        cache_name = "2480_cache" + test_number
        snap = "2480-6"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "0" "'"

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

        try:
            # 4. Create and run the plan
            self.create_plan()
            # 5. create a snapshot
            self.create_snapshot(name=snap)
            self.check_plan_output(message='Create snapshot "L_' +
                                           file_system + '_' +
                                           snap + '" for filesystem '
                                                  '"/vx/' +
                                           file_system + '"')
            snaps.append(snap)
            # 6. check the sfs for the filesystems, snapshot and cache
            self.check_sfs(file_systems, cache_present=False,
                           cache_name=cache_name, snaps=snaps,
                           snap_present=False)

        finally:
            self.clean_sfs(file_systems)
            self.remove_snapshots()

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc07')
    def test_07_p_multiple_filesystems_in_different_states(self):
        """
        This test now covers litpcds_3612_tc04
        #tms_id: litpcds_2480_tc07
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Create and delete multiple filesystems in different states
        #tms_description: Test that ensures we can snap filesystems that
        are in the correct state
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache created
            #step: Create an sfs-filesystem with size=20G, snap_size=10
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem with size=20G, snap_size=10
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem with size=20G, snap_size=10
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem with size=20G, snap_size=10
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem with size=20G, snap_size=0
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Check that the filesystems were created with specified
            properties
            #result: Filesystems are present
            #step: Update the snap_size of filesystem 1 to snap_size=0
            #result: snap_size of filesystem 1 is updated
            #step: Update the snap_size of filesystem 2 to snap_size=100
            #result: snap_size of filesystem 2 is updated
            #step: Remove filesystem 3
            #result: filesystem is removed
            #step: Create snapshot
            #result: Create snapshot is successful
            #step: Check that the filesystems, snapshot and cache are in the
            correct state
            #result: Filesystems, snapshot and cache are present with the
            correct properties
            #step: Update various filesystems
            #result: Filesystem properties updates
            #step: Remove snapshot
            #result: Snapshot is removed
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test07"
        file_systems = []
        file_system1 = "2480-fs1" + test_number + "_a"
        file_systems.append(file_system1)
        path1 = "/vx/" + file_system1
        file_system2 = "2480-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        file_system3 = "2480-fs1" + test_number + "_c"
        file_systems.append(file_system3)
        path3 = "/vx/" + file_system3
        file_system4 = "2480-fs1" + test_number + "_d"
        file_systems.append(file_system4)
        path4 = "/vx/" + file_system4
        file_system5 = "2480-fs1" + test_number + "_e"
        file_systems.append(file_system5)
        path5 = "/vx/" + file_system5
        cache_name = "2480_cache" + test_number
        snap = "2480-7"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem1 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_a"
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_b"
        sfs_filesystem3 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_c"
        sfs_filesystem4 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_d"
        sfs_filesystem5 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number + "_e"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props1 = "path=" + "'" + path1 + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "path=" + "'" + path3 + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props4 = "path=" + "'" + path4 + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "
        sfs_filesystem_props5 = "path=" + "'" + path5 + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "0" "' "
        sfs_filesystem_props1_update = "snap_size=" + "'" "0" "' "
        sfs_filesystem_props1_update2 = "snap_size=" + "'" "20" "' "
        sfs_filesystem_props2_update = "snap_size=" + "'" "100" "' "

        self.log('info', "1. Create an sfs-cache")
        self.create_item(item_path=sfs_cache,
                         item_type="sfs-cache",
                         item_props=sfs_cache_props,
                         xml_path=sfs_cache_xml)

        self.log('info', "2. Create the sfs-filesystems")
        self.create_item(item_path=sfs_filesystem1,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props1,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem2,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props2,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem3,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props3,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem4,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props4,
                         xml_path=sfs_filesystem_xml)
        self.create_item(item_path=sfs_filesystem5,
                         item_type="sfs-filesystem",
                         item_props=sfs_filesystem_props5,
                         xml_path=sfs_filesystem_xml)

        try:
            self.log('info', "3. Create and run the plan")
            self.create_plan()
            self.check_sfs(file_systems)

            self.log('info', "4. Change the filesystems")
            self.update_item(item_path=sfs_filesystem1,
                             item_props=sfs_filesystem_props1_update)
            self.update_item(item_path=sfs_filesystem2,
                             item_props=sfs_filesystem_props2_update)
            self.execute_cli_remove_cmd(self.ms_node, sfs_filesystem3)

            self.log('info', "5. Create a snapshot")
            self.create_snapshot(name=snap)
            snaps.append(snap)

            self.log('info', "6. Ensure the sfs is in the correct state")
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="24576", snaps=snaps)

            self.log('info', "7. Change the filesystems")
            self.update_item(item_path=sfs_filesystem1,
                             item_props=sfs_filesystem_props1_update2)
            self.execute_cli_remove_cmd(self.ms_node, sfs_filesystem5)

            self.log('info', "8. Delete the snapshot")
            self.delete_snapshot(name=snap)
            self.check_sfs(file_systems, snaps=snaps, snap_present=False,
                           cache_name=cache_name, cache_present=False)

        finally:
            self.log('info', "9. Cleanup after the test")
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    #@attr('all', 'revert', 'story2480', 'story2480_tc08')
    def obsolete_08_n_cache_name_must_match_cache_items_name(self):
        """
        Converted to AT "test_08_n_cache_name_must_match_cache_items_name.at"
        in nas
        #tms_id: litpcds_2480_tc08
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Cache name must match cache item's name
        #tms_description: Test that ensures the cache_name on a filesystem
        must match a cache's name
        #tms_test_steps:
            #step: Create an sfs-cache with name='2480_cache_test08'
            #result: sfs-cache created
            #step: Create an sfs-filesystem with cache_name not relevant to
             the above cache; cache_name='incorrect'
            #result: Item is created
            #step: Create plan
            #result: Create plan fails with Validation error
            #result: Expected error message:
            'Create plan failed: The "cache_name" property ' \
                        'value "incorrect" does not match the sfs-cache ' \
                        'item "name" property
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc09')
    def obsolete_09_n_invalid_sfs_cache_name(self):
        """
        Converted to AT "test_09_n_invalid_sfs_cache_name.at" in nasapi
        #tms_id: litpcds_2480_tc09
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Invalid sfs cache name
        #tms_description: Test the creation of a cache with an invalid
        name to verify that this isn't possible
        #tms_test_steps:
            #step: Create a sfs-cache with invalid name:
            name='2480_cache_test09?/'
            #result: Create item fails on validation error
            #result: Expected error message:
            "Invalid value '2480_cache_test09?/'. Accepts only " \
                        "alphanumeric characters and ""-"" and ""_"", " \
                        "minimum 1 maximum 25 characters."
            #step: Create a sfs-cache with invalid name:
            #result: Create item fails on validation error
            #result: Expected error message:
            "Invalid value '2480_cache_test09wwwwwwwwwwwww" \
                         "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww" \
                         "wwwwwwww'. Accepts only alphanumeric characters " \
                         "and ""-"" and ""_"", minimum 1 maximum 25 " \
                         "characters.'"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc10')
    def obsolete_10_n_invalid_filesystem_cache_name(self):
        """
        Converted to AT "test_10_n_invalid_filesystem_cache_name.at" in nasapi
        #tms_id: litpcds_2480_tc10
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Invalid filesystem cache name
        #tms_description: Test that creates an sfs-filesystem with an
        invalid cache_name to verify that it is not possible
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create an sfs-filesystem with an invalid cache_name
            #result: Create item fails
            #result: Expected error message:
            "Invalid value '2480_cache_test09?/'. Accepts only " \
                        "alphanumeric characters and ""-"" and ""_"", " \
                        "minimum 1 maximum 25 characters."
            #step: Create a second sfs-cache with invalid name:
            #result: Create item fails with validation error
            #result: Expected error message:
            "Invalid value '2480_cache_test09wwwwwwwwwwwww" \
                         "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww" \
                         "wwwwwwww'. Accepts only alphanumeric characters " \
                         "and ""-"" and ""_"", minimum 1 maximum 25 " \
                         "characters.'"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc11')
    def obsolete_11_n_properties_must_be_present_with_each_other(self):
        """
        Converted to AT
        "test_11_n_properties_must_be_present_with_each_other.at" in nasapi
        #tms_id: litpcds_2480_tc11
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Properties must be present with each other
        #tms_description: Test that creates an sfs-filesystem without
        having both cache_name and snap_size properties
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create an sfs-file system with an invalid snap_size
            #result: Creation of the above item fails
            #result: Validation error message:
            'Both "snap_size" and "cache_name" properties
                        'must be defined or neither, when creating an
                        '"sfs-filesystem" item.'
            #step: Create an sfs-file system with an invalid snap_size
            #result: Creation of the above item fails
            #result: Validation error message:
            'Both "snap_size" and "cache_name" properties
                        'must be defined or neither, when creating an
                        '"sfs-filesystem" item.'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc12')
    def obsolete_12_n_invalid_snap_size_value(self):
        """
        Converted to AT "test_12_n_invalid_snap_size_value.at" in nasapi
        #tms_id: litpcds_2480_tc12
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Invalid snap size values
        #tms_description: Test that creates an sfs-filesystem with an
        invalid snap_size
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create multiple sfs-file systems with an invalid snap_size
            #result: Creation of the file systems fail with a validation error
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc13')
    def obsolete_13_n_only_one_cache_can_exist(self):
        """
        Converted to AT "test_13_n_only_one_cache_can_exist.at" in nas
        #tms_id: litpcds_2480_tc13
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Only one cache can exist
        #tms_description: This test creates two sfs-caches with same name,
        to prove that only one can exist.
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create another sfs-cache with the same name
            #result: sfs-cache is created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem is created
            #step: Create plan
            #result: Create plan fails
            #result: Error message:
            'Create plan failed: This collection is limited
                        to a maximum of 1 items not marked for removal'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc14')
    def test_14_p_minimum_cache_size(self):
        """
        #tms_id: litpcds_2480_tc14
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Minimum cache size
        #tms_description: This test ensures that we can create a snapshot
        with a name, and the cache will be the minimum size of 6M.
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache is created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem is created
            #step: Create plan
            #result: Plan is running
            #step: Create a named snapshot
            #result: create_snapshot plan succeeds
            #step: Check that the filesystems, snapshot and cache were created
            with the expected properties.
            #result: The file systems are successfully validated
            #result: The cache has the expected minimum size of 6M
            #result: A snapshot with the specified name exists
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test14"
        file_systems = []
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        cache_name = "2480_cache" + test_number
        snap = "2480-14"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10M" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "'"

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

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. create a snapshot
            self.create_snapshot(name=snap)
            snaps.append(snap)
            # 5. check the sfs for the filesystems, snapshot and cache
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="6", snaps=snaps)

        finally:
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    #@attr('all', 'revert', 'story2480', 'story2480_tc15')
    def obsolete_15_n_remove_cache_with_filesystem(self):
        """
        Converted to AT "test_15_n_remove_cache_with_filesystem.at" in nas
        #tms_id: litpcds_2480_tc15
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Remove cache with filesystem
        #tms_description: Test that ensures we cannot remove a cache if a
        filesystem remains in applied state, with a cache_name matching that
        cache
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create and run plan
            #result: Plan is running
            #step: Remove the sfs-cache
            #result: Above item is marked for removal
            #step: Create plan
            #result: Create plan fails with ValidationError
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2480', 'story2480_tc16')
    def obsolete_16_n_filesystem_under_cache(self):
        """
        Converted to AT "test_16_n_filesystem_under_cache.at" in nas
        #tms_id: litpcds_2480_tc16
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Filesystem under cache
        #tms_description: Test the creation of a cache but no filesystem
        referencing it
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache created
            #step: create an sfs-filesystem without specifying cache_name and
            snap_size
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Create plan fails with Validation error:
            #result: "Create plan failed: The sfs-cache item requires a minimum
            of 1 sfs-filesystem item with a property "cache_name" value
            "2480_cache_test16"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc17')
    def test_17_n_create_cache_too_large(self):
        """
        #tms_id: litpcds_2480_tc17
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Create cache too large
        #tms_description: Test that ensures we cannot create a snapshot when
            snap_size is too large for the disk
        #tms_test_steps:
            #step: Create an sfs-cache
            #result: sfs-cache created
            #step: create an sfs-filesystem with size=20G, snap_size=3000
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Run create_snapshot
            #result: The plan fails.
            #result: Error present in logs:
            "Unable to create fs 2480_cache_test17 due to either insufficient
            space/unavailable disk."
            #step: Update the filesystem to size=20G, snap_size=10
            #result: filesystem size and snap_size are updated
            #step: Run create_snapshot
            #result: The snapshot is created
            #step: Ensure the snapshot and cache are on the sfs
            #result: Snapshot and cache are present on the sfs
            #step: update the filesystem to size=20G, snap_size=3000
            #result: Filesystem successfully updated
            #step: Create a snapshot
            #result: Expect the create_snapshot plan to fail
            #result: The logs will contain the following error:
            "Unable to create fs 2480_cache_test17 due to either insufficient
            space/unavailable disk."
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test17"
        file_systems = []
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        cache_name = "2480_cache" + test_number
        snap = "2480-17"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "20G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "3000" "'"
        sfs_filesystem_props2 = "snap_size=" + "'" "10" "'"
        sfs_filesystem_props3 = "snap_size=" + "'" "3000" "'"

        expected_error_logs = ["Unable to create fs " + cache_name + " "
                               "due to either insufficient "
                               "space/unavailable disk."]

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

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. create a snapshot
            self.create_snapshot(plan_pass=False, name=snap)
            # 5. ensure plan fails with correct error in the logs
            self.grep_logs(message=expected_error_logs)
            # 6. update the filesystem to size=20G, snap_size=10
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props2)
            self.remove_snapshots()
            # 7. create a snapshot
            self.create_snapshot(name=snap)
            # 8. ensure snapshot and cache on the sfs
            self.check_sfs(file_systems, cache_name=cache_name,
                           cache_size="2048", snaps=snaps)
            self.remove_snapshots()
            # 9. update the filesystem to size=20G, snap_size=3000
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            # 10. create a snapshot
            self.create_snapshot(plan_pass=False, name=snap)
            # 11. ensure plan fails with correct error in the logs
            self.grep_logs(message=expected_error_logs)

        finally:
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc18')
    def test_18_n_add_snapshot_manually_to_sfs(self):
        """
        #tms_id: litpcds_2480_tc18
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Add snapshot manually to sfs
        #tms_description: Test that ensures we can create snapshot with name
        #tms_test_steps:
            #step: Create an sfs-cache with cache_name='2480_cache_test18'
            #result: sfs-cache created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Create a cache and snapshot of the filesystem manually on
            the sfs with the same name
            #result: Manually created the above
            #step: Run litp create_snapshot
            #result: create_snapshot fails
            #result: Error message will be present in the logs:
            "Rollback L_2480-fs1_test18_2480-18 already exist for
            file system 2480-fs1_test18."
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        test_number = "_test18"
        file_systems = []
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        cache_name = "2480_cache" + test_number
        snap = "2480-18"
        snaps = []
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "'"
        snapshot_name = "L_" + file_system + "_" + snap
        expected_error_logs = ["Rollback " + snapshot_name +
                               " already exist for file system "
                               + file_system + "."]

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

        try:
            # 3. Create and run the plan
            self.create_plan()
            # 4. create a cache and snapshot manually
            self.set_node_connection_data(self.nas_server,
                                      username=test_constants.SFS_MASTER_USR,
                                      password=test_constants.SFS_MASTER_PW)
            self.create_sfs_cache(self.nas_server, cache_name=cache_name,
                                  cache_size="1024M", cache_pool="litp2")
            self.create_sfs_snapshot(self.nas_server,
                                     snapshot_name=snapshot_name,
                                     fs_name=file_system,
                                     cache_name=cache_name)
            # 5. create a snapshot
            self.create_snapshot(plan_pass=False, name=snap)
            # 6. ensure plan fails with correct error in the logs
            self.grep_logs(message=expected_error_logs)

        finally:
            snaps.append(snap)
            self.clean_sfs(file_systems, snaps=snaps, cache_name=cache_name)
            self.remove_snapshots()

    @attr('pre-reg', 'revert', 'story2480', 'story2480_tc19')
    def test_19_n_multiple_caches_under_pool_before_snapshot(self):
        """
        #tms_id: litpcds_2480_tc19
        #tms_requirements_id: LITPCDS-2480
        #tms_title: Multiple caches under pool before snapshot
        #tms_description:
            Test that creates two cache items and multiple filesystems under
            one pool and then tries to snapshot
        #tms_test_steps:
            #step: Create an sfs-cache with cache_name='2480_cache_test19'
            #result: sfs-cache created
            #step: Create an sfs-filesystem
            #result: sfs-filesystem created
            #step: Create an sfs-filesystem with
            cache_name='2480_cache_test19', snap_size=10
            #result: sfs-filesystem created
            #step: Create and run the plan
            #result: Plan is running
            #step: Check that the filesystems were created
            #result: Filesystems are present
            #step: Create another cache with cache_name='2480_cache_test19_b'
            #result: sfs-cache created
            #step: Update the first fs with cache_name='2480_cache_test19_b'
            #result: Cache_name updated
            #step: Run create_snapshot
            #result: ValidationError message is output:
            'Create snapshot failed: All file systems under
                        'every sfs-pool for the sfs-service item on
                        'path "/infrastructure/storage/storage_providers
                        'sfs_service_sp1" must have the same
                        '"cache_name" property value.'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test19"
        file_system = "2480-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "2480-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        cache_name = "2480_cache" + test_number
        cache_name2 = "2480_cache" + test_number + "_b"
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache2 = self.sfs_pools[0] + '/cache_objects/cache_2840_b'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_cache_props2 = "name=" + "'" + cache_name2 + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_2480' \
                          + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                                "size=" + "'" "10G" "' " + \
                                "cache_name=" + "'" + cache_name + "' " + \
                                "snap_size=" + "'" "10" "' "
        sfs_filesystem_props3 = "cache_name=" + "'" + cache_name2 + "' " + \
                                "snap_size=" + "'" "10" "' "
        error_message = 'Create snapshot failed: All file systems under ' \
                        'every sfs-pool for the sfs-service item on ' \
                        'path "/infrastructure/storage/storage_providers/' \
                        'sfs_service_sp1" must have the same ' \
                        '"cache_name" property value.'

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
            # 6. create another cache with cache_name=cache2
            self.create_item(item_path=sfs_cache2,
                             item_type="sfs-cache",
                             item_props=sfs_cache_props2,
                             xml_path=sfs_cache_xml)
            # 7. update the first fs with cache_name=cache2
            self.update_item(item_path=sfs_filesystem,
                             item_props=sfs_filesystem_props3)
            # 8. Run create_snapshot and ensure the correct error is thrown
            self.create_snapshot(expect_positive=False,
                                 error_message=error_message)

        finally:
            self.clean_sfs(file_systems)
