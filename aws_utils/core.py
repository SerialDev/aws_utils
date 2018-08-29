import boto3
import datetime

def start_session(aws_access_key_id, aws_secret_access_key, region_name):
    session = boto3.Session(region_name=region_name,
                                     aws_access_key_id = self.key,
                                     aws_secret_access_key = self.secret,
                                     # aws_session_token=response['Credentials']['SessionToken']
    )
    return session









