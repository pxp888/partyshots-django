import boto3
from botocore.exceptions import ClientError
from .models import Album, Photo, Tag, Subs


# import time 
# from PIL import Image
# import base64 
# import random
# import string
# import io 
import os 



'''AWS S3 functions'''

if os.path.exists('env.py'): import env 


def upload_bytes_to_s3(bytes_data, object_name):
    bucket_name = 'pxp-imagestore'
    s3_client = boto3.client('s3')
    try:
        response = s3_client.put_object(Body=bytes_data, Bucket=bucket_name, Key=object_name)
    except ClientError as e:
        print(e)
        return False
    return True


def upload_file_to_s3(file_name, object_name):
    bucket_name = 'pxp-imagestore'
    s3_client = boto3.client('s3', region_name='eu-north-1')
    try:
        response = s3_client.upload_file(file_name, bucket_name, object_name)
    except ClientError as e:
        print(e)
        return False
    return True


def create_presigned_url(object_name, expiration=604800):
    bucket_name = 'pxp-imagestore'
    s3_client = boto3.client('s3', region_name='eu-north-1')
    try:
        response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
    except ClientError as e:
        print(e)
        return None
    except:
        return None

    return response


def delete_file_from_s3(object_name):
    bucket_name = 'pxp-imagestore'
    s3_client = boto3.client('s3', region_name='eu-north-1')
    try:
        response = s3_client.delete_object(Bucket=bucket_name, Key=object_name)
    except ClientError as e:
        print(e)
        return False
    return True


def cleanup():
    '''This function cleans up the S3 bucket by deleting any files that are not in the database.'''
    bucket_name = 'pxp-imagestore'

    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket_name)

    current = {}
    phots = Photo.objects.all()
    for phot in phots:
        current[phot.link] = True
        current[phot.tlink] = True

    for content in response.get('Contents', []):
        if content['Key'] not in current:
            print('Deleting: ', content['Key'])
            s3_client.delete_object(Bucket=bucket_name, Key=content['Key'])

    print('----------------------\n S3 Cleanup done. \n----------------------')