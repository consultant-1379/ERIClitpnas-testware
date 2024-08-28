obsoleted test cases:

testset_story10974.py test_01_p_create_snapshot_with_two_pools_when_pool_in_initial
Description: <Test that ensures we can create a snapshot is a second pool exists in the model in an initial state>
Reason why obsoleted: Story 10916 allows the functionality that these tests check against
Gerrit review to obsolete test case(s): https://gerrit.ericsson.se/#/c/1186817/

testset_story10974.py test_02_n_create_two_pools_with_filesystems
Description: <Test that ensures we can not create multiple pools>
Reason why obsoleted: Story 10916 allows the functionality that these tests check against
Gerrit review to obsolete test case(s): https://gerrit.ericsson.se/#/c/1186817/

testset_story8524.py test_23_n_one_filesystem_must_exist
Description: <Test that creates an sfs-pool without any filesystems>
Reason why obsoleted: Cardinality rule removed from the nasapi for story 10916
Gerrit review to obsolete test case(s): https://gerrit.ericsson.se/#/c/1189248/

######################################################################
STORY 6817
######################################################################

TEST: test_05_n_reduce_sfs_filesystem_size

DESCRIPTION:
    Test that tries to reduce the size of an sfs-filesystem

REASON OBSOLETED:
    Covered in AT "ats/validation/validate_sfs_filesystem_size_update.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4111886/

TMS-ID:
    litpcds_6817_tc05

-----------------------------------------------------------------------

######################################################################
STORY 2480
######################################################################

TEST: test_01_p_create_snapshot_of_multiple_filesystems

DESCRIPTION:
    Test to ensure that a snapshot can be created

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc01

-----------------------------------------------------------------------

TEST: test_04_p_change_of_snap_size_increases_cache_size

DESCRIPTION:
    Test that ensures when we update a filesystem's
    snap_size and create a snapshot, the cache object is increased in size

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc04

-----------------------------------------------------------------------

TEST: test_05_p_create_cache_that_exists

DESCRIPTION:
    Test that ensures the manual creation of a cache on the sfs

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc05

-----------------------------------------------------------------------

TEST: test_08_n_cache_name_must_match_cache_items_name

DESCRIPTION:
    Test that ensures the cache_name on a filesystem must match a cache's name

REASON OBSOLETED:
    Converted to AT "test_08_n_cache_name_must_match_cache_items_name.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc08

-----------------------------------------------------------------------

TEST: test_09_n_invalid_sfs_cache_name

DESCRIPTION:
    Test the creation of a cache with an invalid name to verify that this
    isn't possible

REASON OBSOLETED:
    Converted to AT "test_09_n_invalid_sfs_cache_name.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc09

-----------------------------------------------------------------------

TEST: test_10_n_invalid_filesystem_cache_name

DESCRIPTION:
    Test that creates an sfs-filesystem with an invalid cache_name to
    verify that it is not possible

REASON OBSOLETED:
    Converted to AT "test_10_n_invalid_filesystem_cache_name.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc10

-----------------------------------------------------------------------

TEST: test_11_n_properties_must_be_present_with_each_other

DESCRIPTION: Test that creates an sfs-filesystem without having both
             cache_name and snap_size properties

REASON OBSOLETED: Converted to AT
                  "test_11_n_properties_must_be_present_with_each_other.at"
                  in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc11

-----------------------------------------------------------------------

TEST: test_12_n_invalid_snap_size_value

DESCRIPTION: Test that creates an sfs-filesystem with an invalid
             snap_size

REASON OBSOLETED:
    Converted to AT "test_12_n_invalid_snap_size_value.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc12

-----------------------------------------------------------------------

TEST: test_13_n_only_one_cache_can_exist

DESCRIPTION:
    This test creates two sfs-caches with same name, to prove that only one
    can exist.

REASON OBSOLETED:
    Converted to AT "test_13_n_only_one_cache_can_exist.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc13

-----------------------------------------------------------------------

TEST: test_15_n_remove_cache_with_filesystem

DESCRIPTION:
    Test that ensures we cannot remove a cache if a filesystem remains
    in applied state, with a cache_name matching that cache

REASON OBSOLETED:
    Converted to AT "test_15_n_remove_cache_with_filesystem.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc15

-----------------------------------------------------------------------

TEST: test_16_n_filesystem_under_cache

DESCRIPTION:
    Test the creation of a cache but no filesystem referencing it

REASON OBSOLETED:
    Converted to AT "test_16_n_filesystem_under_cache.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4042700/

TMS_ID:
    litpcds_2480_tc16
-----------------------------------------------------------------------

######################################################################
STORY 6815
######################################################################

TEST: test_02_p_verify_remove_ipv4allowed_client

DESCRIPTION:
    Test that ensures we can remove an allowed_client from an existing export

REASON OBSOLETED:
    Merged with TC01

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4110666/

TMS-ID:
    litpcds_6815_tc02

-----------------------------------------------------------------------

TEST: test_04_n_verify_remove_all_ipv4allowed_client

DESCRIPTION: Test that tries to remove all the ips from an export

REASON OBSOLETED: Converted to AT
                  "test_04_n_verify_remove_all_ipv4allowed_client.at"
                  in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4110666/

TMS-ID: litpcds_6815_tc04

-----------------------------------------------------------------------

TEST: test_05_n_verify_order_ipv4allowed_clients

DESCRIPTION:
    Test that tries to change the order of ip in the allowed clients list

REASON OBSOLETED:
    Converted to AT "test_05_n_verify_order_ipv4allowed_clients.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4110666/

TMS-ID:
    litpcds_6815_tc05

-----------------------------------------------------------------------

TEST: test_06_n_remove_client_with_mount

DESCRIPTION:
    Test that removes a mounted client from the allowed clients list of
    an export

REASON OBSOLETED:
    Converted to AT "test_06_n_remove_client_with_mount.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4110666/

TMS-ID:
    litpcds_6815_tc06

-----------------------------------------------------------------------

######################################################################
STORY 8062
######################################################################

TEST: test_04_n_create_invalid_subnet

DESCRIPTION:
    Test that creates an export with an invalid subnet

REASON OBSOLETED:
    Converted to AT "test_04_n_create_invalid_subnet.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4112372/

TMS-ID:
    litpcds_8062_tc04

-----------------------------------------------------------------------

TEST: test_10_n_share_with_subnet_and_ip_within_subnet

DESCRIPTION:
    Test that creates an export with a subnet and an ip within the subnet

REASON OBSOLETED:
    Converted to AT "test_10_n_share_with_subnet_and_ip_within_subnet.at"
    in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4112372/

TMS-ID:
    litpcds_8062_tc10

-----------------------------------------------------------------------

TEST: test_11_n_shares_with_conflicing_ip_and_subnet

DESCRIPTION:
    Test that creates two exports with conflicting allowed clients

REASON OBSOLETED:
    Converted to AT "test_11_n_shares_with_conflicing_ip_and_subnet.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4112372/

TMS-ID:
    litpcds_8062_tc11

-----------------------------------------------------------------------

######################################################################
STORY 8524
######################################################################

TEST: test_08_n_create_duplicate_vip

DESCRIPTION:
    Test that creates duplicate virtual servers

REASON OBSOLETED:
    Converted to AT "ats/validation/validate_misc.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc08

-----------------------------------------------------------------------

TEST: test_09_n_invalid_vip_name

DESCRIPTION:
    Test that creates a vip with an invalid name

REASON OBSOLETED:
    Converted to AT "test_09_n_invalid_vip_name.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc09

-----------------------------------------------------------------------

TEST: test_10_n_invalid_vip_ipv4address

DESCRIPTION:
    Test that creates a vip with an invalid ipv4address

REASON OBSOLETED: "ipv4address" defined in core so it not appropriate
                  to test this in nasapi.

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc10

-----------------------------------------------------------------------

TEST: test_11_n_create_duplicate_services

DESCRIPTION:
    Test that creates two sfs-services with the same ip

REASON OBSOLETED:
    Converted to AT "test_11_n_create_duplicate_services.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc11

-----------------------------------------------------------------------

TEST: test_12_n_login_details_must_exist

DESCRIPTION:
    Test that creates an sfs-service without the login details

REASON OBSOLETED:
    Converted to AT "test_12_n_login_details_must_exist.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc12

-----------------------------------------------------------------------

TEST: test_13_n_create_service_with_invalid_key

DESCRIPTION:
    Test that creates an sfs-service with an invalid key

REASON OBSOLETED:
    Converted to AT "test_13_n_create_service_with_invalid_key.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc13

-----------------------------------------------------------------------

TEST: test_14_n_create_service_with_invalid_user

DESCRIPTION:
    Test that creates an sfs-service with an invalid user

REASON OBSOLETED:
    Converted to AT "test_14_n_create_service_with_invalid_user.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc14

-----------------------------------------------------------------------

TEST: test_15_n_create_an_sfs_service_with_user_does_not_exist

DESCRIPTION:
    Test that creates a SFS service with an incorrect username property

REASON OBSOLETED:
    n/a

GERRIT LINK:
    n/a

TMS-ID:
    n/a

-----------------------------------------------------------------------

TEST: test_16_n_create_duplicate_pools

DESCRIPTION:
    Test that creates duplicate sfs-pools

REASON OBSOLETED:
    Converted to AT "test_16_n_create_duplicate_pools.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc16

-----------------------------------------------------------------------

TEST: test_17_n_pool_must_exist

DESCRIPTION:
    Test that checks an error is given when creating a filesystem
    under a sfs-service

REASON OBSOLETED:
    Converted to AT "test_17_n_pool_must_exist.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc17

-----------------------------------------------------------------------

TEST: test_18_n_pool_name_required

DESCRIPTION:
    Test that creates an sfs-pool without the pool_name property

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc18

-----------------------------------------------------------------------

TEST: test_19_n_invalid_pool_name

DESCRIPTION:
    Test that creates an sfs-pool with an invalid pool_name

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc19

-----------------------------------------------------------------------

TEST: test_20_n_invalid_pool_name_length

DESCRIPTION:
    Test that creates an sfs-pool with an invalid pool_name

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc20

-----------------------------------------------------------------------

TEST: test_21_n_create_invalid_pool_name

DESCRIPTION:
    Test that creates an sfs-pool with an invalid pool_name

REASON OBSOLETED:
    Test has been made obsolete due to story 10974 being implemented.
    this functionality is being tested inside the following
    unit test:
    test_fs_resize_callback

GERRIT LINK: Obsoleted prior to refactoring

TMS-ID:
    n/a

-----------------------------------------------------------------------

TEST: test_22_n_create_duplicate_filesystems

DESCRIPTION:
    Tests user cannot create duplicate filesystems

REASON OBSOLETED:
    Converted to AT "ats/validation/validate_misc.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc22

-----------------------------------------------------------------------

TEST: test_24_n_filesystem_must_exist

DESCRIPTION:
    Test that creates an export under an sfs-pool

REASON OBSOLETED:
    Converted to AT "test_24_n_filesystem_must_exist.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc24

-----------------------------------------------------------------------

TEST: test_25_n_filesystem_requires_size

DESCRIPTION:
    Test that creates an sfs-filesystem without the
    "size" parameter

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc25

-----------------------------------------------------------------------

TEST: test_27_n_filesystem_valid_size_start

DESCRIPTION:
    Test that creation fails for sfs-filesystems with invalid sizes

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc27

-----------------------------------------------------------------------

TEST: test_28_n_filesystem_valid_size_end

DESCRIPTION:
    Test that attempts to create sfs-filesystem with invalid sizes

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc28

-----------------------------------------------------------------------

TEST: test_29_n_filesystem_requires_path

DESCRIPTION:
    Test that creates sfs-filesystems without a path

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc29

-----------------------------------------------------------------------

TEST: test_30_n_filesystem_with_invalid_path_character

DESCRIPTION:
    Test that creates sfs-filesystems with an invalid path character

REASON OBSOLETED:
    Converted to AT "test_30_n_filesystem_with_invalid_path_character.at"
    in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc30

-----------------------------------------------------------------------

TEST: test_31_n_filesystem_path_over_max_length

DESCRIPTION:
    Test that creates sfs-filesystems with a "path" that's too long

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc31

-----------------------------------------------------------------------

TEST: test_32_n_filesystem_with_incorrect_prefix

DESCRIPTION:
    Test that creates sfs-filesystems with a "path" that's too long

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc32

-----------------------------------------------------------------------

TEST: test_33_n_create_duplicate_export

DESCRIPTION:
    Test that creates duplicate sfs-exports

REASON OBSOLETED:
    Converted to AT "test_33_n_create_duplicate_export.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc33

-----------------------------------------------------------------------

TEST: test_34_n_export_requires_allowed_clients

DESCRIPTION:
    Test that attempts to create sfs-export without "ip4allowed_clients" set

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc34

-----------------------------------------------------------------------

TEST: test_35_n_export_with_invalid_ipv4_range

DESCRIPTION:
    Test that attempts to create an export with invalid ipv4 range

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc35

-----------------------------------------------------------------------

TEST: test_36_n_create_export_with_invalid_ipv4allowed_clients

DESCRIPTION:
    Test that creates an export's allowed_clients with an invalid deliminator

REASON OBSOLETED:
    Converted to AT
    "test_36_n_create_export_with_invalid_ipv4allowed_clients.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc36

-----------------------------------------------------------------------

TEST: test_37_n_export_with_invalid_allowed_clients_not_ipv4s

DESCRIPTION:
    Test that creates an export with invalid allowed_clients

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc37

-----------------------------------------------------------------------

TEST: test_38_n_create_conflicting_exports

DESCRIPTION:
    Test that attempts to create conflicting exports
    and ensure expected eror generated

REASON OBSOLETED:
    Converted to AT "test_38_n_create_conflicting_exports.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc38

-----------------------------------------------------------------------

TEST: test_39_n_create_export_with_duplicate_allowed_clients

DESCRIPTION:
    Test that creates an export with invalid allowed_clients

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc39

-----------------------------------------------------------------------

TEST: test_40_n_export_requires_options

DESCRIPTION:
    Test that creates an export without the "options" parameter

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc40

-----------------------------------------------------------------------

TEST: test_41_n_export_invalid_deliminator_options

DESCRIPTION:
    Test that creates an export with invalid deliminator "options" parameter

REASON OBSOLETED:
    Converted to AT "test_41_n_export_invalid_deliminator_options.at" in
    nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc41

-----------------------------------------------------------------------

TEST: test_42_n_conflicting_export_options

DESCRIPTION:
    Test that creates an export with conflicting "options" parameter

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc42

-----------------------------------------------------------------------

TEST: test_43_n_invalid_mount_provider

DESCRIPTION:
    Test that creates an nfs-mount with the "provider" that doesn't
    match a vip parameter

REASON OBSOLETED:
    Converted to AT "test_43_n_invalid_mount_provider.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc43

-----------------------------------------------------------------------

TEST: test_45_n_create_export_with_invalid_allowed_ip

DESCRIPTION:
    Test that creates an nfs-mount on a invalid ip

REASON OBSOLETED:
    Converted to AT "test_45_n_create_export_with_invalid_allowed_ip.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc45

-----------------------------------------------------------------------

TEST: test_46_n_invalid_mount_mount_options

DESCRIPTION:
    Test that creates an nfs-mount with an invalid option delimiter

REASON OBSOLETED:
    Converted to AT "test_46_n_invalid_mount_mount_options.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc46

-----------------------------------------------------------------------

TEST: test_47_n_duplicate_mount_mount_options

DESCRIPTION:
    Test that creates an nfs-mount with duplicate options

REASON OBSOLETED:
    Converted to AT "test_47_n_duplicate_mount_mount_options.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc47

-----------------------------------------------------------------------

TEST: test_48_n_conflicting_mount_mount_options

DESCRIPTION:
    Test that creates an nfs-mount with conflicting options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc48

-----------------------------------------------------------------------

TEST: test_49_n_invalid_mount_options_value

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Converted to AT "test_49_n_invalid_mount_options_value.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc49

-----------------------------------------------------------------------

TEST: test_50_n_invalid_sec_mount_option

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc50

-----------------------------------------------------------------------

TEST: test_51_n_invalid_proto_mount_option

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc51

-----------------------------------------------------------------------

TEST: test_52_n_invalid_lookupcache_mount_option

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc52

-----------------------------------------------------------------------

TEST: test_53_n_invalid_clientaddr_mount_option

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc53

-----------------------------------------------------------------------

TEST: test_54_n_invalid_timeo_mount_option

DESCRIPTION:
    Test that creates an nfs-mount with invalid options

REASON OBSOLETED:
    Covered in AT "ats/property_types_review.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4115779/

TMS-ID:
    litpcds_8524_tc54

-----------------------------------------------------------------------

######################################################################
STORY 12032
######################################################################

TEST: test_02_n_update_nfs_mounts_provider_to_incorrect_values

DESCRIPTION:
    Test that ensures you can't update an nfs-mount's provider to
    an invalid value

REASON OBSOLETED:
    Converted to AT
    "test_02_n_update_nfs_mounts_provider_to_incorrect_values.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4117726/

TMS-ID:
    litpcds_12032_tc02

-----------------------------------------------------------------------
=======
STORY 5284
######################################################################

TEST: test_02_p_create_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on the peer
             nodes.

REASON OBSOLETED:
    Merged with
    test_03_p_create_sfs_unmanaged_mnts_nodes_in_diff_directories.

GERRIT LINK:

TMS-ID: litpcds_5284_tc02

-----------------------------------------------------------------------
TEST: test_05_p_create_non_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on each node

REASON OBSOLETED:
    Merged with
    test_06_p_create_non_sfs_unmanaged_mounts_nodes_in_diff_dirs

GERRIT LINK:

TMS-ID: litpcds_5284_tc05

-----------------------------------------------------------------------
TEST: test_07_p_remove_sfs_unmanaged_mount

DESCRIPTION:
    Remove a SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc07

-----------------------------------------------------------------------

TEST: test_08_p_remove_non_sfs_unmanaged_mount

DESCRIPTION:
    Remove non SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC06

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc08

-----------------------------------------------------------------------

TEST: test_13_n_sfs_unmanaged_mount_mandatory

DESCRIPTION:
    Test that when creating a sfs_unmanaged_mount, the required properties,
    when not entered, throw up the correct error.

REASON OBSOLETED:
    Converted to AT "test_13_n_sfs_unmanaged_mount_mandatory.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc13

-----------------------------------------------------------------------

TEST: test_14_n_non_sfs_unmanaged_mount_mandatory

DESCRIPTION:
    Test that when creating a non_sfs_unmanaged_mount,
    the required properties, when not entered, throw up the correct error.

REASON OBSOLETED:
    Converted to AT "test_14_n_non_sfs_unmanaged_mount_mandatory.at" in
    nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc14

-----------------------------------------------------------------------

TEST: test_15_n_non_sfs_unmanaged_mount_ipaddress_validation

DESCRIPTION:
    Test that when creating a non_sfs_unmanaged_mount,
    when creating the nfs_service, the IPv4 and IPv6 are validated.

REASON OBSOLETED:
    Converted to AT "test_15_n_non_sfs_unmanaged_mount_ipaddress_validation.at"
    in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc15

-----------------------------------------------------------------------

TEST: test_16_n_sfs_unmanaged_mount_export_path_validation

DESCRIPTION:
    Test that when creating a non_sfs_unmanaged_mount,
    any export_path with an invalid value will throw an error at item
    creation.

REASON OBSOLETED:
    Converted to AT "test_16_n_sfs_unmanaged_mount_export_path_validation.at"
    in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc16

-----------------------------------------------------------------------

TEST: test_17_n_non_sfs_unmanaged_mount_export_path_validation

DESCRIPTION:
    Test that when creating a non sfs unmanaged_mount,
    when creating the nfs_mount, it should fail.

REASON OBSOLETED:
    Converted to AT
    "test_17_n_non_sfs_unmanaged_mount_export_path_validation.at" in nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc17

-----------------------------------------------------------------------

TEST: test_18_n_unmanaged_mount_point_validation

DESCRIPTION:
    Test that when creating an unmanaged_mount,
    when creating the nfs_mount, it should fail.

REASON OBSOLETED:
    Converted to test "test_18_n_unmanaged_mount_point_validation.at" in
    nasapi

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc18

-----------------------------------------------------------------------

TEST: test_19_n_unmanaged_mount_server_name_duplication

DESCRIPTION:
    Test that checks conflicting name properties for
    an unmanaged mount.

REASON OBSOLETED:
    Converted to "test_19_n_unmanaged_mount_server_name_duplication.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc19

-----------------------------------------------------------------------

TEST: test_20_n_sfs_unmanaged_mount_mount_point_duplication

DESCRIPTION:
    Test that when creating a sfs-unmanaged_mount,
    when creating the nfs_mounts, it should fail when there
    are duplicate mount points.

REASON OBSOLETED:
    Converted to "test_20_n_sfs_unmanaged_mount_mount_point_duplication.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc20

-----------------------------------------------------------------------

TEST: test_21_n_non_sfs_unmanaged_mount_mount_point_duplication

DESCRIPTION:
    Test that when creating an non-sfs-unmanaged_mount,
    when creating the nfs_mounts, it should fail when there
    are duplicate mount points.

REASON OBSOLETED:
    Covered in AT
    "ats/validation/validate_nested_mount_points.at" in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc21

-----------------------------------------------------------------------

TEST: test_22_n_sfs_unmanaged_mount_missing_provider

DESCRIPTION:
    Test the creation of an sfs-unmanaged_mount,
    when creating the nfs_mounts, set the provider as a
    different name than the vip.

REASON OBSOLETED:
    Converted to AT "test_22_n_sfs_unmanaged_mount_missing_provider.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc22

-----------------------------------------------------------------------

TEST: test_23_n_non_sfs_unmanaged_mount_missing_provider

DESCRIPTION:
    Test that when creating an non-sfs-unmanaged_mount,
    when creating the nfs_mounts, it should fail when there
    is duplicate mount points.

REASON OBSOLETED:
    Converted to AT "test_23_n_non_sfs_unmanaged_mount_missing_provider.at"
    in nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc23

-----------------------------------------------------------------------

TEST: test_24_n_unmanaged_mount_provider_duplication

DESCRIPTION:
    Test the creation of a sfs-unmanaged_mount,
    and then creating a non-sfs-unmanaged mount,
    and a nfs mount with conflicting names/provider

REASON OBSOLETED:
    Converted to AT "test_24_n_unmanaged_mount_provider_duplication.at" in
    nas

GERRIT LINK:
    https://gerrit.ericsson.se/#/c/4105610/

TMS-ID:
    litpcds_5284_tc24

-----------------------------------------------------------------------
