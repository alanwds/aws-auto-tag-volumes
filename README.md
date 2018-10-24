# AWS Auto Tag Volumes

# Description

This script will search for untagged volumes. If there are, the script will find the instance id attach to this volume, get the specified tag+value and add tag=value on volume. This is very usefull since AWS do not tag volumes created by ASG group. 

# Authentication

The script use boto, so, if you already have aws/credentials file, the script will work's fine. You can use env variables also:

|Variable|Description|
|--------|-----------|
|DEBUG|Enabled debug mode (print a lot of information)
|REQUIRED_TAG|Tag to search|
|AWS_DEFAULT_REGION| Your AWS REGION|
|AWS_ACCESS_KEY_ID|Your AWS Key|
|AWS_SECRET_ACCESS_KEY|Your AWS SECRET KEY|

# Usage

./aws-auto-tag-volumes.py requiredTAG

# Docker

docker run --rm -e DEBUG="1" -e REQUIRED_TAG="MyCostCenter" -e AWS_DEFAULT_REGION="XXXX" -e AWS_ACCESS_KEY_ID="XXXXXX" -e AWS_SECRET_ACCESS_KEY="XXXXX" alanwds/aws-auto-tag-volumes:latest

######

PR, comments and enhancements are always welcome
