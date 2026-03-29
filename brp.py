#!/usr/bin/env python3
"""
Bike Ride Publisher

Publishes ride CSV files to AWS S3, uploading only new or changed files.
"""

import argparse
import configparser
import hashlib
from pathlib import Path

CSV_DIR = "/Users/chris/git/darringer-bikelog/data/rides"
CONFIG_FILE = Path(__file__).parent / 'bikelog.ini'


def load_config():
    """Load configuration from bikelog.ini."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Config file not found: {CONFIG_FILE}\n"
            "Create bikelog.ini with:\n"
            "  [s3]\n"
            "  bucket = your-bucket-name\n"
            "  region = us-east-1\n"
            "  prefix = rides/"
        )
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def _md5_of_file(filepath):
    """Compute MD5 hash of a file."""
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def publish_to_s3():
    """Publish CSV files to S3, uploading only new or changed files."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("Error: boto3 is required for S3 publishing.")
        print("Install it with: pip install boto3")
        return

    config = load_config()
    bucket = config.get('s3', 'bucket')
    region = config.get('s3', 'region', fallback=None)
    prefix = config.get('s3', 'prefix', fallback='rides/')
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    local_files = sorted(Path(CSV_DIR).glob('rides_*.csv'))
    if not local_files:
        print("No CSV files found to publish.")
        return

    s3 = boto3.client('s3', region_name=region)

    # Fetch existing S3 object ETags for the prefix
    s3_etags = {}
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                s3_etags[obj['Key']] = obj['ETag'].strip('"')
    except ClientError as e:
        print(f"Error accessing S3 bucket '{bucket}': {e}")
        return

    uploaded = 0
    skipped = 0
    for local_path in local_files:
        s3_key = prefix + local_path.name
        local_md5 = _md5_of_file(local_path)
        if s3_key in s3_etags and s3_etags[s3_key] == local_md5:
            skipped += 1
        else:
            action = "Updating" if s3_key in s3_etags else "Uploading"
            print(f"  {action} {local_path.name}...")
            s3.upload_file(str(local_path), bucket, s3_key)
            uploaded += 1

    print(f"Publish complete: {uploaded} uploaded, {skipped} unchanged.")


def main():
    parser = argparse.ArgumentParser(
        description='Publish bike ride CSV files to S3'
    )
    parser.parse_args()
    publish_to_s3()


if __name__ == '__main__':
    main()
