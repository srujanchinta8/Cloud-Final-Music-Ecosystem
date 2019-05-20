import json
import boto3
import os
from contextlib import closing

import uuid

lec_client = boto3.client('lex-runtime')
polly_client = boto3.client('polly')

bucketName = 'cloud-project-audiobucket'

def lambda_handler(event, context):

    print(event)
    requestBody = json.loads(event['body'])
    
    lexResponse = lec_client.post_text(
        botAlias = 'cloud_project_chatbot_alias',
        botName = 'cloud_project_chatbot',
        userId =  "456",
        inputText = requestBody['message']['content']['text'],
        sessionAttributes={
            'general_key': requestBody['message']['content']['spotify_token']
            }
        )
    
    print(lexResponse)
    
    statusCode = lexResponse['ResponseMetadata']['HTTPStatusCode']
    responseText = lexResponse['message']
    
    recordId = str(uuid.uuid4())
    
    response = polly_client.synthesize_speech(
        OutputFormat='mp3',
        Text = responseText,
        VoiceId = 'Joanna'
    )
    
    if "AudioStream" in response:
        with closing(response["AudioStream"]) as stream:
            output = os.path.join("/tmp/", recordId)
            with open(output, "ab") as file:
                file.write(stream.read())
                
    s3 = boto3.client('s3')
    s3.upload_file('/tmp/' + recordId, bucketName, recordId + ".mp3")
    
    #responseText = '1: Is YouTube also contributing in digital waste? https://t.co/c4C15Q56Mt #Marketing 2: RT @Conqueroo1: ICYMI: Blues Music Awards 2019 Winners Announced: Shemekia Copeland, Michael Ledbetter Lead Winners https://t.co/PrfG2X9kpK 3: RT @dpbrelsford: country music just hits different when it’s 75° and my windows are down'
        
    if('track_url' in lexResponse['sessionAttributes']):
        result = {
            'statusCode':statusCode,
            'body':"{\"result\": {\"text\" : \"" + responseText + "\", \"s3_uuid\" : \"" + recordId + "\", \"track_url\" : \"" + lexResponse['sessionAttributes']['track_url'] + "\" }}",
            'headers': {
                "Content-Type" : "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Allow" : "GET, OPTIONS, POST",
                "Access-Control-Allow-Methods" : "GET, OPTIONS, POST",
                "Access-Control-Allow-Headers" : "*"
            }
        }
    else:
        result = {
            'statusCode':statusCode,
            'body':"{\"result\": {\"text\" : \"" + responseText + "\", \"s3_uuid\" : \"" + recordId + "\" }}",
            'headers': {
                "Content-Type" : "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Allow" : "GET, OPTIONS, POST",
                "Access-Control-Allow-Methods" : "GET, OPTIONS, POST",
                "Access-Control-Allow-Headers" : "*"
            }
        }
        
    
    print(result)
    return result