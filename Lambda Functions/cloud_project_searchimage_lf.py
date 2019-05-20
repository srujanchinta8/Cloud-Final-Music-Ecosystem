import json
import boto3
from botocore.vendored import requests
import spotipy

def lambda_handler(event, context):
    requestBody = json.loads(event['body'])
    filename = requestBody['image_name']
    token = requestBody['spotify_token']
    
    bucket='cloud-project-imagebucket'
    client=boto3.client('rekognition')
    print("loaded client")
    response = client.recognize_celebrities(Image={'S3Object':{'Bucket':bucket,'Name':filename}})
    
    celebrity = response['CelebrityFaces'][0]['Name']
    print(celebrity)
    
    spotify = spotipy.Spotify(auth=token)
    result = spotify.search(celebrity, type="artist", limit=10)
    artists = result['artists']['items']
    if len(artists) != 0:
	    artist = artists[0]
	    result = spotify.artist_top_tracks(artist['uri'])
	    celebrity = celebrity + " who top 5 tracks are "
	    i = 0
	    for track in result['tracks'][:5]:
		    print(track['name'], track['external_urls']['spotify'])
		    i += 1
		    celebrity = celebrity + " " + str(i) + ") " + track['name']
    else:
        celebrity = celebrity + " Not a music artist."
		
    result = {
        'statusCode':'200',
        'body':"{\"result\": \"" + celebrity + "\"}",
        'headers': {
            "Content-Type" : "application/json",
            "Access-Control-Allow-Origin" : "*",
            "Allow" : "GET, OPTIONS, POST",
            "Access-Control-Allow-Methods" : "GET, OPTIONS, POST",
            "Access-Control-Allow-Headers" : "*"
        }
    }
    return result