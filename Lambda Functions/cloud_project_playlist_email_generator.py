import json
import boto3
import random
import string
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    #song_id_list - hardcoded for now, will be input from generated playlist
    '''song_id_list = ['spotify:track:3BQHpFgAp4l80e1XslIjNI', 'spotify:track:6ORqU0bHbVCRjXm9AjyHyZ', 'spotify:track:4wzjNqjKAKDU82e8uMhzmr']
    post_song_ids_to_queue(song_id_list)
    '''
    message = "No playlist to generate!"
    
    song_id_list, email = get_messages_from_queue()
    
    if song_id_list:
        song_list = retrieve_from_db(song_id_list)
        if email:
            sendSesEmail(song_list, email)
        message = "Email sent"
    
    
    
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

def retrieve_from_db(song_id_list):
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('final-project-songs')
    result = []
    for song in song_id_list:
        print (song)
        response = table.get_item(Key={'SongID': song})
        print (response)
        if response:
            result.append(response["Item"])
    print (result)
    return result
    
def post_song_ids_to_queue(s_id_list):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='cloud_project_song_id.fifo')
    song_id_list = ' '.join(s_id_list)
    response=queue.send_message(MessageBody='To be retrieved from dynamo', MessageAttributes={
    'song_id_list': {
        'StringValue': song_id_list,
        'DataType': 'String'
        },
    'email': {
        'StringValue': "vatsala.swaroop@gmail.com",
        'DataType': 'String'
        }
    },
    MessageGroupId=''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]),
    MessageDeduplicationId=''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
    )    
    return "IDs posted"
    

def sendSesEmail(dynamo_result, email):
    client = boto3.client("sns")
    # This address must be verified with Amazon SES.
    SENDER = "vatsala.swaroop@columbia.edu"
    
    # this address must be verified.
    RECIPIENT = email

    AWS_REGION = "us-east-1"
    client = boto3.client('ses',region_name=AWS_REGION)
    
    # The subject line for the email.
    SUBJECT = "Music Ecosystem : Your Playlist is here!"
    
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (""
                )
                
    table_str = ""
    if dynamo_result:
        table_str = table_str + "<table style= \"background-color: #F6F6F6;\">" + "<tr style= \"background-color: #4CAF50;\"><th>Song Name</th><th>Artist</th><th>Duration (sec)</th></tr>"
        for song in dynamo_result:
            table_str = table_str + "<tr>"
            table_str = table_str + "<td>" + song['Name'] + "</td>"
            table_str = table_str + "<td>" + song['Artist'] + "</td>" + "<td>" + str(song['Duration']) + "</td>"
            table_str = table_str + "</tr>"
        table_str = table_str + "</table>"
    
    print(table_str)
                
    # The HTML body of the email.
    BODY_HTML = """<html><head>
    <style>td,th {border: 1px solid #ddd;padding: 8px;
    }th {color:white;
    }</style>
    </head>
    <body>
      <h2>We have recommended the following songs for you!</h2>""" + "</br>"+table_str
    """</body>
    </html>"""
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Try to send the email.
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

    
def get_messages_from_queue():
    
    queue_url = "	https://sqs.us-east-1.amazonaws.com/854667354389/cloud_project_song_id.fifo"
    
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue = sqs.get_queue_by_name(QueueName='cloud_project_song_id.fifo')
    
    response = queue.receive_messages(MessageAttributeNames=['song_id_list', 'email'])
    print(response)
    
    receipt_handle = None
    song_id_list = []
    
    for r in response:
        song_id_list = r.message_attributes.get('song_id_list').get('StringValue')
        email = r.message_attributes.get('email').get('StringValue')
        receipt_handle = r.receipt_handle
    
    if receipt_handle != None:
        resp = client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        
    final_list = []
    if song_id_list:
        final_list = song_id_list.split()
    
    print("fetched_song_id_list", final_list)
    return final_list, email