#!/usr/bin/env sh

if [ -z "$1" ]; then
    echo "ERROR: Set AWS S3 Bucket mount dir"
    exit 1
fi

if [ -z "$2" ]; then
    echo "ERROR: Set AWS S3 Bucket exported GPKG dir"
    exit 1
fi

AWS_S3_BUCKET_MNT_DIR=$1
AWS_S3_BUCKET_GPKG_EXPORT_DIR=$2

create_aws_credentials () {
    mkdir -p $HOME/.aws
    echo "$DPNK_AWS_ACCESS_KEY_ID:$DPNK_AWS_SECRET_ACCESS_KEY" > $HOME/.passwd-s3fs
    chmod 600 $HOME/.passwd-s3fs
}

create_aws_credentials
s3fs $DPNK_AWS_STORAGE_BUCKET_NAME $AWS_S3_BUCKET_MNT_DIR
mkdir -p "$AWS_S3_BUCKET_MNT_DIR/$AWS_S3_BUCKET_GPKG_EXPORT_DIR"
