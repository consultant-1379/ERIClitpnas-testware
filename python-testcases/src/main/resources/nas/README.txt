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
STORY 5284
######################################################################

TEST: test_02_p_create_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on the peer
             nodes.

REASON OBSOLETED:
    Merged with
    test_03_p_create_sfs_unmanaged_mnts_nodes_in_diff_directories.

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID: litpcds_5284_tc02

-----------------------------------------------------------------------
TEST: test_05_p_create_non_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on each node

REASON OBSOLETED:
    Merged with
    test_06_p_create_non_sfs_unmanaged_mounts_nodes_in_diff_dirs

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID: litpcds_5284_tc05

-----------------------------------------------------------------------
TEST: test_07_p_remove_sfs_unmanaged_mount

DESCRIPTION:
    Remove a SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc07

-----------------------------------------------------------------------

TEST: test_08_p_remove_non_sfs_unmanaged_mount

DESCRIPTION:
    Remove non SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC06

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc08

-----------------------------------------------------------------------

TEST: test_13_n_sfs_unmanaged_mount_mandatory

DESCRIPTION:
    Test that when creating a sfs_unmanaged_mount, the required properties,
    when not entered, throw up the correct error.

REASON OBSOLETED:
    Converted to AT "test_13_n_sfs_unmanaged_mount_mandatory.at" in nasapi

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc24

-----------------------------------------------------------------------
######################################################################
STORY 5284
######################################################################

TEST: test_02_p_create_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on the peer
             nodes.

REASON OBSOLETED:
    Merged with
    test_03_p_create_sfs_unmanaged_mnts_nodes_in_diff_directories.

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID: litpcds_5284_tc02

-----------------------------------------------------------------------
TEST: test_05_p_create_non_sfs_unmanaged_mounts_nodes

DESCRIPTION: Test the creation of SFS unmanaged mounts on each node

REASON OBSOLETED:
    Merged with
    test_06_p_create_non_sfs_unmanaged_mounts_nodes_in_diff_dirs

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID: litpcds_5284_tc05

-----------------------------------------------------------------------
TEST: test_07_p_remove_sfs_unmanaged_mount

DESCRIPTION:
    Remove a SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC03

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc07

-----------------------------------------------------------------------

TEST: test_08_p_remove_non_sfs_unmanaged_mount

DESCRIPTION:
    Remove non SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC06

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc08

-----------------------------------------------------------------------

TEST: test_13_n_sfs_unmanaged_mount_mandatory

DESCRIPTION:
    Test that when creating a sfs_unmanaged_mount, the required properties,
    when not entered, throw up the correct error.

REASON OBSOLETED:
    Converted to AT "test_13_n_sfs_unmanaged_mount_mandatory.at" in nasapi

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

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

GERRIT LINK: https://gerrit.ericsson.se/#/c/4913328/

TMS-ID:
    litpcds_5284_tc24

-----------------------------------------------------------------------

######################################################################
STORY 3612
######################################################################

TEST: test_01_p_remove_snapshots_of_multiple_filesystems

DESCRIPTION: Test that ensures we can remove a snapshot

REASON OBSOLETED: Merged with TC03 of story2480

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID: litpcds_3612_tc01

-----------------------------------------------------------------------

TEST: test_02_p_remove_snapshot_with_a_name

DESCRIPTION: Test that ensures we can remove a snapshot with a name

REASON OBSOLETED: Merged with TC02 of story2480

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID: litpcds_3612_tc02

-----------------------------------------------------------------------

TEST: test_03_p_remove_snapshot_manually

DESCRIPTION:
    Test that ensures we can remove a snapshot manually

REASON OBSOLETED: Merged with TC03 of story2480

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID: litpcds_3612_tc03

-----------------------------------------------------------------------

TEST: test_04_p_remove_snapshots_in_different_states

DESCRIPTION: Test that ensures we can remove snapshots of filesystems in
             different states

REASON OBSOLETED: Merged with TC07 of story2480

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID: litpcds_3612_tc04

-----------------------------------------------------------------------
######################################################################
STORY 4154
######################################################################

TEST: test_01_p_ensure_share_created

DESCRIPTION: Test that ensures we can create a share

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_02_n_create_duplicate_export

DESCRIPTION:
    Test that ensures we cannot create an export that already exists

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_03_n_create_export_with_invalid_pool

DESCRIPTION:
    Test that creates an export with an invalid pool_name

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_04_p_create_export_and_mount

DESCRIPTION:
    Test that creates an export and a mount

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_05_p_create_export_and_one_mount

DESCRIPTION:
    Test that creates multiple exports but mounts to one

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_06_n_create_export_with_invalid_allowed_ip

DESCRIPTION:
    Test that creates an sfs-export with an invalid allowed_client ip

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_07_n_create_conflicting_exports

DESCRIPTION:
    Test that creates two exports with the same export_path

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_08_n_mount_export_path_not_matching_export

DESCRIPTION:
    Test that has an incorrect export_path for the nfs_mount than the export

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_09_p_create_export_and_mount_with_multiple_ips

DESCRIPTION:
    Test that creates a managed sfs-export with a list of allowed_clients

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_10_n_export_with_invalid_ipv4allowed_clients_range

DESCRIPTION:
    Test that creates an sfs-export with ipv4allowed_clients that contains
    a range

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_11_n_export_with_invalid_allowed_clients_not_comma

DESCRIPTION:
    Test that creates an sfs-export with ipv4allowed_clients that
    doesn't contain commas

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_12_n_export_with_invalid_allowed_clients_not_ipv4s

DESCRIPTION:
    Test that creates an sfs-export with ipv4allowed_clients that
    doesn't contain valid ip4s

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_13_n_export_with_invalid_ipv6allowed_clients_range

DESCRIPTION:
    Test that creates an sfs-export with ipv6allowed_clients
    that contains a range

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_14_n_export_invalid_ipv6allowed_clients_not_comma

DESCRIPTION:
    Test that creates an sfs-export with ipv6allowed_clients that
    doesn't contain commas

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_15_n_export_with_invalid_allowed_clients_not_ipv6s

DESCRIPTION:
    Test that creates an sfs-export with ipv6allowed_clients that
    doesn't contain valid ip6s

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_16_n_create_service_with_invalid_key

DESCRIPTION:
    Test that creates an sfs-service with an invalid key

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_17_n_create_service_with_invalid_user

DESCRIPTION:
    Test that creates an sfs-service with an invalid user

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_18_n_create_export_with_size_larger_than_pool

DESCRIPTION:
    Test that creates an sfs-export with a larger than available size

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_19_n_export_with_invalid_sysid

DESCRIPTION:
    Test that creates an sfs-export with an invalid sysid

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_20_n_export_with_invalid_file_system

DESCRIPTION:
    Test that creates an sfs-export with an invalid file_system

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_21_n_export_with_no_hyphen

DESCRIPTION:
    Test that creates an sfs-export without a hyphen

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_22_n_export_over_max_length

DESCRIPTION:
    Test that creates an sfs-export that's too long

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_23_n_export_with_incorrect_prefix

DESCRIPTION:
    Test that creates an sfs-export with an incorrect prefix

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_24_n_login_details_must_exist

DESCRIPTION:
    Test that creates an sfs-service without the login details

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_25_n_pool_name_required

DESCRIPTION:
    Test that creates an sfs-service without the pool_name property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_27_n_export_path_required

DESCRIPTION:
    Test that creates an sfs-export without the export_path property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_28_n_export_requires_allowed_clients

DESCRIPTION:
    Test that creates an sfs-export without the export_path property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_29_n_export_requires_export_options

DESCRIPTION:
    Test that creates an sfs-export without a export_options property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_30_n_export_valid_export_options

DESCRIPTION:
    Test that creates an sfs-export with invalid export_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_31_n_export_conflicting_export_options

DESCRIPTION:
    Test that creates an sfs-export with export_options that conflict

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_32_n_export_requires_size

DESCRIPTION:
    Test that creates an sfs-export without the required "size" property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_33_n_export_valid_size_start

DESCRIPTION:
    Test that creates an sfs-export with an invalid value for "size"

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_34_n_export_valid_size_end

DESCRIPTION:
    Test that creates an sfs-export with an invalid value for "size"

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_35_n_invalid_mount_provider

DESCRIPTION:
    Test that creates an nfs-mount with a invalid provider

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_36_n_invalid_mount_export_path

DESCRIPTION:
    Test that creates an nfs-mount with a invalid export_path

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_37_n_invalid_mount_mount_options

DESCRIPTION:
    Test that creates an nfs-mount with invalid mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_38_n_conflicting_mount_mount_options

DESCRIPTION:
    Test that creates an nfs-mount with conflicting mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_39_n_invalid_mount_options_value

DESCRIPTION:
    Test that creates an nfs-mount with a invalid mount_option

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_40_n_invalid_sec_mount_option

DESCRIPTION:
    Test that creates an nfs-mount and has an invalid "sec" value in
    mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_41_n_invalid_proto_mount_option

DESCRIPTION:
    Test that creates an nfs-mount and has an invalid "proto" value in
    mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_42_n_invalid_lookupcache_mount_option

DESCRIPTION:
    Test that creates an nfs-mount and has an invalid "lookupcache"
    property in mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_43_n_invalid_clientaddr_mount_option

DESCRIPTION:
    Test that creates an nfs-mount and has an invalid "clientaddr"
    value in mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_44_n_invalid_timeo_mount_option

DESCRIPTION:
    Test that creates an nfs-mount and has conflicting properties with
    the "timeo" property in mount_options

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_45_n_create_sfs_service_with_ipv4_and_ipv6

DESCRIPTION:
    Test that creates a service with both management_ip's

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_46_n_create_vip_with_ipv4_and_ipv6

DESCRIPTION:
    Test that creates a vip with both management_ip's

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_47_n_create_export_with_ipv4_and_ipv6

DESCRIPTION:
    Test that creates a export with both ipallowed_clients

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_48_n_create_export_with_ipv6_under_ipv4

DESCRIPTION:
    Test that creates an ipv6 export with a ipv4 service and vip

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_49_n_create_vip_with_ipv6_under_ipv4

DESCRIPTION:
    Test that creates an ipv6 vip with a ipv4 service and export

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_50_n_create_export_with_ipv4_under_ipv6

DESCRIPTION:
    Test that creates an ipv4 export with a ipv6 service and vip

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_51_n_create_vip_with_ipv4_under_ipv6

DESCRIPTION:
    Test that creates an ipv4 vip with a ipv6 service and export

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_52_n_two_sfs_service_with_duplicate_management_ipv4s

DESCRIPTION:
    Test that creates two sfs services with duplicate management IPv4
    addresses

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_53_n_two_sfs_service_with_duplicate_management_ipv6s

DESCRIPTION:
    Test that creates two sfs services with duplicate management IPv6
    addresses

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_54_n_create_an_sfs_service_with_user_does_not_exist

DESCRIPTION:
    Test that creates a SFS service with an incorrect username property

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

TEST: test_55_p_two_exports_with_different_allowed_clients

DESCRIPTION:
    Test that creates 2 exports with different allowed clients

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a
-----------------------------------------------------------------------

TEST: test_56_n_create_share_that_already_exists

DESCRIPTION:
    Test that tries to create a share that already exists with a
    different size

REASON OBSOLETED: Obsoleted prior to the refactoring project

GERRIT LINK: n/a

TMS-ID: n/a

-----------------------------------------------------------------------

######################################################################
STORY 5985
######################################################################

TEST: test_1_p_remove_sfs_unmanaged_mount_on_ms

DESCRIPTION:
    Remove a SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC01 of story5284

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID:
    litpcds_5985_tc01

-----------------------------------------------------------------------

TEST: test_2_p_remove_non_sfs_unmanaged_mount_on_ms

DESCRIPTION:
    Remove a non-SFS unmanaged mount and ensure that the mount is deleted

REASON OBSOLETED:
    Merged with TC04 of story5284

GERRIT LINK: https://gerrit.ericsson.se/#/c/4877707/

TMS-ID:
    litpcds_5985_tc02
