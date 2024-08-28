"""
@copyright: Ericsson Ltd
@since:     July 2016
@author:    erogehi
@summary:   Tests for NAS plugin bug:
            TORF-126316
"""
import re

import test_constants
from litp_generic_test import GenericTest, attr
from xml_utils import XMLUtils


class BugTorf126316(GenericTest):
    """
    TORF-126316: ENM upgrade fail after SFS Failover to node 2

    NasPlugin now generates a new task to get and save the host key from the
    remote vip NAS head, every time a CallbackTask needs naslib to connects
    over SSH. This will make sure that MS will keep the required host keys
    saved in known_hosts file.
    """

    ssh_find_regex = re.compile(
                     r'#\s*Host\s+[\w\.\-]+\s+found:\s+line\s+[\w\-]+')

    def setUp(self):
        """ Run before every test """
        super(BugTorf126316, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.nas_server = self.get_sfs_node_filenames()[0]
        self.xml = XMLUtils()
        self.sfs_pools = self.find(self.ms_node, "/infrastructure", "sfs-pool")

    def tearDown(self):
        """Run after every test"""
        super(BugTorf126316, self).tearDown()

    def xml_validator(self, item_path, load_path,
                      file_name="xml_bug126316.xml"):
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

    def get_number_of_entries_in_known_hosts_file(self, host):
        """ Uses the command sh-keygen -F to know how many entries of a certain
        host is in the file.
        """
        cmd = 'su celery -c "ssh-keygen -F {0}"'.format(host)
        out, _, code = self.run_command(self.ms_node, cmd, su_root=True)
        self.assertEquals(code, 0, out)
        hosts = [l for l in out if self.ssh_find_regex.match(l)]
        return len(hosts)

    def clean_known_hosts_file(self, host):
        """ Uses the command sh-keygen -R to remove a certain host from the
        known_hosts file.
        """
        cmd = 'su celery -c "ssh-keygen -R {0}"'.format(host)
        out, _, code = self.run_command(self.ms_node, cmd, su_root=True)
        self.assertEquals(code, 0, out)

    def generate_new_private_host_key_in_sfs(self):
        """ Uses the command sh-keygen -f to generate private host keys on the
        NAS server.
        """
        host = self.nas_server
        self.set_node_connection_data(host, username='support',
                                      password='symantec')
        self.run_command(host, "rm /etc/ssh/ssh_host_rsa_key; "
                               "rm /etc/ssh/ssh_host_dsa_key; "
                               "rm /etc/ssh/ssh_host_key")

        cmd = "ssh-keygen -f /etc/ssh/ssh_host_rsa_key -N '' -t rsa"
        code = self.run_command(host, cmd)[-1]
        self.assertEquals(code, 0)
        cmd = "ssh-keygen -f /etc/ssh/ssh_host_dsa_key -N '' -t dsa"
        code = self.run_command(host, cmd)[-1]
        self.assertEquals(code, 0)
        cmd = "ssh-keygen -f /etc/ssh/ssh_host_key -N '' -t rsa1"
        code = self.run_command(host, cmd)[-1]
        self.assertEquals(code, 0)
        # remove the known_hosts file from root user on NAS server to avoid
        # host key mismatch.
        code = self.run_command(host, "rm /root/.ssh/known_hosts")[-1]
        self.assertEquals(code, 0)

    @attr('all', 'revert', 'bug126316', 'bug126316_tc01')
    def test_01_p_simulate_sfs_failover(self):
        """
        @tms_id: torf_126316_tc01
        @tms_requirements_id: LITPCDS-6548
        @tms_title: Simulate SFS failover
        @tms_description:
            Test that ensures that NasPlugin will still be able to run
            tasks using naslib to connect to SFS over SSH even if SFS server
            changes its host key. This is a simulation of failover, when the
            other node will return a different remote host key back to naslib.
            The task to change file system size should still work even after
            changing the SFS private host key (simulation of failover).
            Also, the ~/.ssh/known_hosts should have 2 entries related to the
            *same* SFS management_ipv4.
        NOTE: This verifies task TORF-126316
        @tms_test_steps:
            @step: Remove any SFS host key related in ./ssh/known_hosts
            @result: The SFS host key is removed from ./ssh/known_hosts
            @step: Remove all snapshots
            @result: All snapshot are removed
            @step: Create an sfs-filesystem
            @result: sfs-filesystem created
            @step: Create and run the plan
            @result: Plan is running
            @step: Ensure file system is created
            @result: File system is present
            @step: Ensure that just 1 entry is in the ~/.ssh/known_hosts file
            @result: Only 1 entry is found in the ~/.ssh/known_hosts file
            @step: Connect to SFS nas head to re-generate its private host key
            @result: SSH key is re-generated as per successful command status
            @step: Change the file system size
            @result: Size property of sfs-filesystem is changed
            @step: Create and run the plan
            @result: Plan is running
            @step: Ensure that 2 entries is in the ~/.ssh/known_hosts file
            @result: 2 entries related to the same SFS are found in the file
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        test_number = "test01"
        fs_name = "fs1_torf126316_%s" % test_number
        file_systems = [fs_name]
        pool = self.sfs_pools[0]
        item_path = "%s/file_systems/%s" % (pool, fs_name)
        xml_path = "%s/file_systems" % pool

        sfs_servs = self.find(self.ms_node, "/infrastructure", "sfs-service")
        sfs_properties = self.get_props_from_url(self.ms_node, sfs_servs[0])
        mg_ip = sfs_properties['management_ipv4']

        # 1. Remove any SFS host key related in ./ssh/known_hosts
        self.clean_known_hosts_file(mg_ip)
        # 2. Remove all snapshots
        self.remove_all_snapshots(node=self.ms_node)
        # 3. Create an sfs-filesystem
        self.create_item(item_path=item_path, item_type="sfs-filesystem",
                         item_props="path='/vx/%s' size='1G'" % fs_name,
                         xml_path=xml_path)

        try:
            # 4. Create and run the plan
            self.create_plan()
            # 5. Ensure file system is created
            self.check_sfs(file_systems)
            # 6. Ensure that just 1 entry is in the ~/.ssh/known_hosts file
            # related to the SFS management_ipv4.
            num_entries = self.get_number_of_entries_in_known_hosts_file(mg_ip)
            self.assertEquals(num_entries, 1)
            # 7. Connect to SFS nas head to re-generate its private host key.
            self.generate_new_private_host_key_in_sfs()
            # 8. Change the filesystem size
            self.execute_cli_update_cmd(self.ms_node, item_path, "size='2G'")
            # 9. Create and run the plan
            self.create_plan()
            # 10. Ensure that 2 entries is in the ~/.ssh/known_hosts file
            # related to the *same* SFS management_ipv4.
            num_entries = self.get_number_of_entries_in_known_hosts_file(mg_ip)
            self.assertEquals(num_entries, 2)
        finally:
            self.clean_sfs(file_systems)
