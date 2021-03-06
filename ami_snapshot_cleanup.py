#!/usr/bin/env python

import os
import re
import argparse

from boto import ec2


class c:
    HEADER = u"\033[95m"
    OKBLUE = u"\033[94m"
    OKGREEN = u"\033[92m"
    WARNING = u"\033[93m"
    FAIL = u"\033[91m"
    ENDC = u"\033[0m"
    BOLD = u"\033[1m"
    UNDERLINE = u"\033[4m"


def get_snapshots_from_images(images):
    '''Each AMI can have several mapped devices. We take the snapshots.'''

    snapshot_ids = []
    for image in images:
        print "\t\t", c.OKBLUE, image.id, c.ENDC, image.name
        for block_device in image.block_device_mapping:
            bd = image.block_device_mapping[block_device]
            if bd.snapshot_id is not None:
                # print "\t\t\t", c.OKBLUE, bd.snapshot_id, c.ENDC,
                # print bd.size, bd.volume_type
                snapshot_ids.append(bd.snapshot_id)
    return snapshot_ids


def diff_snapshots(all_snapshots, used_snapshot_ids, filter):
    '''Get the snapshots that are not used in an AMI,
    plus an additional filter.'''

    out = []
    for snapshot in all_snapshots:
        # print "\tTrying:", c.OKBLUE, snapshot.id, c.ENDC,
        # print snapshot.description
        if snapshot.id not in used_snapshot_ids and \
                re.search(filter, snapshot.description):
            out.append(snapshot)
    return out


def cleanup_snapshots(snapshots, dry_run=False):
    '''Delete the unused snapshots.'''

    print "\tDeleting:", c.OKGREEN, len(snapshots), c.ENDC, "snapshots"
    cleanup_count = 0
    for snapshot in snapshots:
        print "\tDeleting:", c.OKBLUE, snapshot.id, c.ENDC,
        print snapshot.description
        try:
            out = snapshot.delete(True)
            print out
            cleanup_count += 1
        except Exception, e:
            print "\t\tError:", c.WARNING, e.message, c.ENDC
    return cleanup_count


def main():

    parser = argparse.ArgumentParser(
        description='Garbage collect snapshots unattached to AMIs.')
    parser.add_argument('--user-id', action='store', required=True,
                        help='The AWS user id for the owner of the images.')
    parser.add_argument('--filter', action='store',
                        help='Filter the images to delete by a regex.')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Don\'t actually delete the snapshots.')
    args = parser.parse_args()

    DRY_RUN = args.dry_run
    AWS_USER_ID = args.user_id
    FILTER = args.filter
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    SUPPORTED_REGIONS = ["us-east-1", "us-west-1", "us-west-2"]

    regions = ec2.regions()
    cleanup_count = 0
    for region in regions:
        if region.name not in SUPPORTED_REGIONS:
            print "Skipping", c.OKBLUE, region.name, c.ENDC
            continue

        print "Trying", c.OKBLUE, region.name, c.ENDC, ":"

        conn = region.connect(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
            )

        try:
            images = conn.get_all_images(
                # image_ids=None,
                # image_ids=["ami-abcd1234",],
                owners=[AWS_USER_ID, "self"],
                # executable_by=None,
                # filters=None,
                # filters=["tag:Component="],
                dry_run=False
                )
            print "\t", "Found:", c.OKGREEN, len(images), c.ENDC,
            print "snapshots in images"
            used_snapshot_ids = get_snapshots_from_images(images)

        except Exception, e:
            print "\t", c.WARNING, "Error:", e.message, c.ENDC

        try:
            all_snapshots = conn.get_all_snapshots(
                owner=[AWS_USER_ID, "self"],  # or self
                # filters=None,
                dry_run=False
                )
            print "\t", "Found:", c.OKGREEN, len(all_snapshots),
            print c.ENDC, "snapshots"

        except Exception, e:
            print "\t", c.WARNING, "Error:", e.message, c.ENDC

        diffed_snapshots = diff_snapshots(
            all_snapshots,
            used_snapshot_ids,
            filter=FILTER
            )
        cleanup_count += cleanup_snapshots(diffed_snapshots, dry_run=DRY_RUN)

    print "Deleted", c.OKGREEN, cleanup_count, c.ENDC, "snapshots"

if __name__ == "__main__":
    main()
