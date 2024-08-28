"""
@copyright: Ericsson Ltd
@since:     June 2015
@author:    etomgly
@summary:   Tests for NAS plugin bug:
            LITPCDS-10193
"""
from litp_generic_test import GenericTest, attr
import test_constants
from xml_utils import XMLUtils


class Bug10193(GenericTest):
    """
    LITPCDS-10193:
        SFS remove_snapshot fails if snaps are online on SFS
    """

    def setUp(self):
        """Run before every test"""
        super(Bug10193, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")
        self.timeout_mins = 3

    def tearDown(self):
        """Run after every test"""
        super(Bug10193, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_bug10193.xml"):
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

    def remove_snapshots(self):
        """
        Deletes all snapshots
        """
        snapshot_url = self.find(self.ms_node, "/snapshots",
                              "snapshot-base", assert_not_empty=False)

        list_of_snaps = []
        for snap in snapshot_url:
            if snap == "/snapshots/snapshot":
                self.execute_cli_removesnapshot_cmd(self.ms_node)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, self.timeout_mins))

            else:
                snapshot_name = snap.split("/snapshots/").pop()
                list_of_snaps.append(snapshot_name)

        if list_of_snaps:
            for snap in list_of_snaps:
                args = "-n " + snap
                self.execute_cli_removesnapshot_cmd(self.ms_node, args=args)

                # 1.b Verify that the remove snapshot plan succeeds.
                self.assertTrue(self.wait_for_plan_state(self.ms_node,
                    test_constants.PLAN_COMPLETE, self.timeout_mins))

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

    @attr('all', 'revert', 'bug10193', 'bug10193_tc01')
    def test_01_p_remove_an_online_snapshot(self):
        """
        Description:
            Test that ensures we can remove an online sfs snapshot
        Steps:
        1. create an sfs-cache
        2. create an sfs-filesystem with a size of 10G
        3. create an sfs-filesystem with a size of 10G and snap_size of 10
        4. Create and run the plan
        5. Ensure filesystem are created
        6. Run create_snapshot
        7. Manually online the snapshot on the sfs
        8. Run remove_snapshot
        9. Ensure the plan passes and the snap is removed from the
        sfs and model
        Results:
            Snapshot should be removed even if it's in an online state
        """
        self.remove_snapshots()
        file_systems = []
        test_number = "_test01"
        file_system = "10193-fs1" + test_number
        file_systems.append(file_system)
        path = "/vx/" + file_system
        file_system2 = "10193-fs1" + test_number + "_b"
        file_systems.append(file_system2)
        path2 = "/vx/" + file_system2
        snap_name = "L_" + file_system2 + "_"
        snaps = [snap_name]
        cache_name = "10193_cache" + test_number
        sfs_cache = self.sfs_pools[0] + '/cache_objects/cache_2840'
        sfs_cache_xml = self.sfs_pools[0] + '/cache_objects'
        sfs_cache_props = "name=" + "'" + cache_name + "'"
        sfs_filesystem = self.sfs_pools[0] + '/file_systems/fs1_10193' \
                         + test_number
        sfs_filesystem2 = self.sfs_pools[0] + '/file_systems/fs1_10193' \
                         + test_number + "_b"
        sfs_filesystem_xml = self.sfs_pools[0] + '/file_systems'
        sfs_filesystem_props = "path=" + "'" + path + "' " + \
                               "size=" + "'" "10G" "'"
        sfs_filesystem_props2 = "path=" + "'" + path2 + "' " + \
                               "size=" + "'" "10G" "' " + \
                               "cache_name=" + "'" + cache_name + "' " + \
                               "snap_size=" + "'" "10" "' "

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
            # 6. Run create_snapshot
            self.create_snapshot()
            # 7. Manually online the snapshot on the sfs
            self.assertTrue(self.sfs_rollback_online_snapshot(
                sfs_node=self.nas_server, snap_name=snap_name))
            # 8. Run remove_snapshot
            self.delete_snapshot()
            # 9. Ensure the filesystems are the correct size on the sfs
            self.check_sfs(file_systems, snap_present=False, snaps=snaps)

        finally:
            self.clean_sfs(file_systems)
