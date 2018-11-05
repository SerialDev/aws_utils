import datetime

import boto3


def start_session(aws_access_key_id, aws_secret_access_key, region_name):
    session = boto3.Session(
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        # aws_session_token=response['Credentials']['SessionToken']
    )
    return session
