#!/usr/bin/env python3
"""Upload a file to any S3-compatible storage and return the public URL.

Required env vars:
  S3_BUCKET              - Bucket name
  AWS_ACCESS_KEY_ID      - Access key
  AWS_SECRET_ACCESS_KEY  - Secret key

Optional env vars:
  S3_ENDPOINT_URL        - Custom endpoint for DO Spaces, Cloudflare R2, Backblaze B2, etc.
  S3_PREFIX              - Key prefix (default: "pretty-page/")
  AWS_DEFAULT_REGION     - Region (default: "us-east-1")
  S3_PUBLIC_BASE_URL     - Override the public base URL (e.g. your CDN domain)

Usage:
  python3 upload.py <file-path> [s3-key]

Examples:
  python3 upload.py /tmp/pretty-page-report.html
  python3 upload.py /tmp/pretty-page-report.html my-reports/report.html
"""
import os
import sys


def upload(file_path, key=None):
    try:
        import boto3
    except ImportError:
        print("Error: boto3 not installed. Run: pip install boto3", file=sys.stderr)
        sys.exit(1)

    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        print("Error: S3_BUCKET environment variable not set", file=sys.stderr)
        sys.exit(1)

    endpoint_url = os.environ.get("S3_ENDPOINT_URL")
    prefix = os.environ.get("S3_PREFIX", "pretty-page/")
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    public_base_url = os.environ.get("S3_PUBLIC_BASE_URL")

    if not key:
        key = prefix + os.path.basename(file_path)

    client_kwargs = {"region_name": region}
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    s3 = boto3.client("s3", **client_kwargs)

    content_type = "text/html" if file_path.endswith(".html") else "application/octet-stream"
    s3.upload_file(
        file_path,
        bucket,
        key,
        ExtraArgs={"ACL": "public-read", "ContentType": content_type},
    )

    if public_base_url:
        url = f"{public_base_url.rstrip('/')}/{key}"
    elif endpoint_url:
        # For DO Spaces: endpoint is https://<region>.digitaloceanspaces.com
        # Public URL is: https://<bucket>.<region>.digitaloceanspaces.com/<key>
        # For other providers, set S3_PUBLIC_BASE_URL explicitly.
        from urllib.parse import urlparse
        parsed = urlparse(endpoint_url)
        host = parsed.netloc
        url = f"{parsed.scheme}://{bucket}.{host}/{key}"
    else:
        # Standard AWS S3
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    print(url)
    return url


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file-path> [s3-key]", file=sys.stderr)
        sys.exit(1)

    upload(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
