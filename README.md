# AMI Snapshot Cleanup

This cool tool cleans up snapshots that are not currently tied to an AMI.

## Install

    > pip install -r requirements.txt

## Usage

    > export AWS_ACCESS_KEY=<YOUR_AWS_ACCESS_KEY>
    > export AWS_SECRET_KEY=<YOUR_AWS_SECRET_KEY>
    > ./ami_snapshot_cleanup.py --user-id=123456789123 --dry-run
    
    > ./ami_snapshot_cleanup.py --user-id=123456789123 --filter="Created by CreateImage"

You can also edit the file to change the supported regions (`SUPPORTED_REGIONS`), currently set to `us-east-1`, `us-west-1`, and `us-west-2`.

Applying a `--filter` only deletes snapshots who's description matches the filter regex.
