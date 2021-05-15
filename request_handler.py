import json
import boto3
import os
import logging
import uuid

supported_formats = {"jpg", "jpeg", "png", "bmp", "tif", "txt"}

def request_handler(event: dict, context):
    print(event)
    s3 = boto3.client('s3')
    bucket = os.environ['s3_bucket']
    ext = event['queryStringParameters']['ext']
    if ext not in supported_formats:
        return {
            'isBase64Encoded': False,
            'statusCode': 400,
            'body': json.dumps({'ERROR': 'InvalidFileType'}),
            "headers": {"Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json"}
        }
    unique_id = f"{uuid.uuid4()}"
    folder_name = ''

    s3.put_object(Body=json.dumps(event['queryStringParameters']),
                  Bucket=bucket, Key=f'{folder_name}{unique_id}.json')

    params = {'Bucket': bucket, 'Key': f'{folder_name}{unique_id}.{ext}'}
    try:
        response = s3.generate_presigned_post(bucket, params['Key'])
        #response = s3.generate_presigned_url('put_object', params)
    except ClientError as e:
        logging.error(e)
        return None
    # {'response' : response, 'uuid': f'{folder_name}{unique_id}'}
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': json.dumps(response),
        "headers": {"Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"}
    }
