"""
@copyright: Ericsson Ltd
@since:     January 2015
@author:    etomgly
@summary:   Test for NAS plugin bug:
            LITPCDS-8236
"""
from litp_generic_test import GenericTest, attr


class Bug8236(GenericTest):
    """
    LITPCDS-8236:
        No validation to prevent removal of a sfs-service
        item which is required by existing nfs-mount items
    """

    def setUp(self):
        """Run before every test """
        super(Bug8236, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.sfs_services = self.find(self.ms_node, "/infrastructure",
                                "sfs-service")

    def tearDown(self):
        """Run after every test"""
        super(Bug8236, self).tearDown()

    @attr('all', 'revert', 'story5284', 'story5284_tc01', 'cdb_priority1')
    def test_01_p_remove_service_with_mount(self):
        """
        Description:
        Create SFS unmanaged mount on the MS
        Steps:
        Actions:
            1. Create SFS service
            2. Create /test1 mount
            3. Mount filesystem on the MS
            4. create and run plan
            5. Remove sfs-service
            6. Create plan
            7. ensure correct error is thrown
        Results:
            Create plan should fail and the correct error should be thrown
        """
        # 1. Remove sfs-service
        self.execute_cli_remove_cmd(self.ms_node, self.sfs_services[0])

        try:
            # 2. create plan
            _, stderr, _ = self.execute_cli_createplan_cmd(
                self.ms_node, expect_positive=False)

            # 3. ensure correct error is thrown
            self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                            'Create plan failed: sfs-service "sfs" is '
                            'required by the nfs-mount "' +
                            "/infrastructure/storage/nfs_mounts/mount2" +
                            '" and cannot be removed.')

        finally:
            # 4. Re-add the service
            self.execute_cli_create_cmd(self.ms_node,
                                        self.sfs_services[0], "sfs-service",
                                        add_to_cleanup=False)
