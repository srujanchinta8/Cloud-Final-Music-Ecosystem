import json
import os
import time
import boto3
from botocore.vendored import requests
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import string

def get_slots(intent_request):
	return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
	print(slot_to_elicit)
	return {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'ElicitSlot',
			'intentName': intent_name,
			'slots': slots,
			'slotToElicit': slot_to_elicit,
			'message': message
		}
	}

def close(session_attributes, fulfillment_state, message):
	response = {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'Close',
			'fulfillmentState': fulfillment_state,
			'message': message
		}
	}

	return response

def delegate(session_attributes, slots):
	return {
		'sessionAttributes': session_attributes,
		'dialogAction': {
			'type': 'Delegate',
			'slots': slots
		}
	}


def parse_int(n):
	try:
		return int(n)
	except ValueError:
		return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
	if message_content is None:
		return {
			"isValid": is_valid,
			"violatedSlot": violated_slot,
		}

	return {
		'isValid': is_valid,
		'violatedSlot': violated_slot,
		'message': {'contentType': 'PlainText', 'content': message_content}
	}


def isvalid_date(date):
	try:
		dateutil.parser.parse(date)
		return True
	except ValueError:
		return False

def lambda_handler(event, context):
	"""
	Route the incoming request based on intent.
	The JSON body of the request is provided in the event slot.
	"""
	# By default, treat the user request as coming from the America/New_York time zone.
	try:
		os.environ['TZ'] = 'America/New_York'
		time.tzset()
	except e:
		print("This is an error message!")
	return dispatch(event)

def dispatch(intent_request):
	"""
	Called when the user specifies an intent for this bot.
	"""

	#logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

	intent_name = intent_request['currentIntent']['name']

	# Dispatch to your bot's intent handlers
	if intent_name == 'OrderFlowers':
		return "in orderflowers"
	if intent_name == 'searchTwitter':
		return searchTwitter(intent_request)
	if intent_name == 'searchSpotify':
		return searchSpotify(intent_request)
	if intent_name == 'GreetingsIntent':
		return greeting(intent_request)
	if intent_name == 'playSpotify':
		return playSpotify(intent_request)

	raise Exception('Intent with name ' + intent_name + ' not supported')
	
def getTweetsByHashTag(hashTag):
	
	tweet_str = ""
	
	base_url = 'https://api.twitter.com/'

	search_headers = {
		'Authorization': 'Bearer {}'.format('AAAAAAAAAAAAAAAAAAAAAHqw%2BQAAAAAAWiio154TtDSQ6W4esx2S8XYZNbw%3DXTB9ifO8gDE1LQhlcbKww5U3TZG7B3s3VLtF1HQjzmojMDdnzB')    
	}
	
	search_params = {
		'q': hashTag,
		'result_type': 'recent',
		'count': 10,
		'lang':'en'
	}
	
	search_url = '{}1.1/search/tweets.json'.format(base_url)
	
	search_resp = requests.get(search_url, headers=search_headers, params=search_params)

	print(search_resp.status_code)
	tweet_data = search_resp.json()
	i = 1
	print(tweet_data['statuses'])
	for x in tweet_data['statuses']:
		if i>2:
			return tweet_str
		snt = getSentiment(x['text'])
		twt = preprocess_tweet(x['text'])
		#snt = getSentiment(twt)
		tweet_str = tweet_str+ str(i)+": "+ twt+"___ this tweet is: "+snt+" "
		i = i+1
	print(tweet_str)

	return tweet_str 
	
def getSentiment(text):
	comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
 
	print('Calling DetectSentiment')
	#snt_str = json.dumps(comprehend.detect_sentiment(Text=text, LanguageCode='en'), sort_keys=True, indent=4)
	snt_str = comprehend.detect_sentiment(Text=text, LanguageCode='en')
	print(snt_str)
	return snt_str['Sentiment']

def preprocess_tweet(text_string):

	space_pattern = '\s+'
	giant_url_regex = ('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|'
		'[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
	#mention_regex = '@[\w\-]+'
	#hashtag_regex = '#[\w\-]+'
	alpha_regex = '[^a-zA-Z0-9_#.,@]'
	parsed_text = re.sub(space_pattern, ' ', str(text_string))
	parsed_text = re.sub(giant_url_regex, ' ', parsed_text)
	#parsed_text = re.sub(mention_regex, ' ', parsed_text)
	#parsed_text = re.sub(hashtag_regex, ' ', parsed_text)
	parsed_text = re.sub(alpha_regex, ' ', parsed_text)
	parsed_text = re.sub(alpha_regex, ' ', parsed_text)
	parsed_text = re.sub('  ', ' ', parsed_text)

	return parsed_text

def validate_hashTag(hashTag):
	
	#if searchKey is not None and searchKey not in searchKeys:
	if hashTag is None:
		return build_validation_result(False,
									   'hashTag',
									   'We do not have the tags for {}, would you like to search in for a different topic? ')

	return build_validation_result(True, None, None)
	
def searchTwitter(intent_request):
	
	source = intent_request['invocationSource']
	
	hashTag = intent_request['currentIntent']['slots']['hashTag']
	
	if source == 'DialogCodeHook':
		# Perform basic validation on the supplied input slots.
		# Use the elicitSlot dialog action to re-prompt for the first violation detected.
		slots = get_slots(intent_request)
	   
		validation_result =   validate_hashTag(hashTag)
		if not validation_result['isValid']:
			slots[validation_result['violatedSlot']] = None
			return elicit_slot(intent_request['sessionAttributes'],
							   intent_request['currentIntent']['name'],
							   slots,
							   validation_result['violatedSlot'],
							   validation_result['message'])

		# Pass the price of the flowers back through session attributes to be used in various prompts defined
		# on the bot model.
		output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
		# if flower_type is not None:
		#     output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

		return delegate(output_session_attributes, get_slots(intent_request))
	
	if source == 'FulfillmentCodeHook':
		
		tweets=getTweetsByHashTag(hashTag)
  
		# Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
		# In a real bot, this would likely involve a call to a backend service.
		return close(intent_request['sessionAttributes'],
					'Fulfilled',
					{'contentType': 'PlainText',
					'content': tweets})
					
def validate_trackName(trackName):
	if trackName is None:
		return build_validation_result(False,
									   'trackName',
									   'We do not have the tags for {}, would you like to search in for a different topic? ')

	return build_validation_result(True, None, None)
					
def playSpotify(intent_request):
	
	source = intent_request['invocationSource']
	
	trackName = intent_request['currentIntent']['slots']['trackName']
	
	if source == 'DialogCodeHook':
		slots = get_slots(intent_request)
	   
		validation_result = validate_trackName(trackName)
		if not validation_result['isValid']:
			slots[validation_result['violatedSlot']] = None
			return elicit_slot(intent_request['sessionAttributes'],
							   intent_request['currentIntent']['name'],
							   slots,
							   validation_result['violatedSlot'],
							   validation_result['message'])

		output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
		return delegate(output_session_attributes, get_slots(intent_request))
	
	if source == 'FulfillmentCodeHook':
		token = intent_request['sessionAttributes']['general_key']
		spotify = spotipy.Spotify(auth=token)
		
		results = spotify.search(trackName, type="track", limit=10)
		if(len(results["tracks"]["items"]) != 0):
			track = results["tracks"]["items"][0]
			print(track['name'], track['artists'][0]['name'], track['preview_url'])
			if(track['preview_url'] != None):
			    intent_request['sessionAttributes']['track_url'] = track['preview_url']
			    return_string = 'Here is song ' + track['name'] + ' by ' + track['artists'][0]['name']
			else:
			    return_string = 'Spotify Premium needed for song ' + track['name'] + ' by ' + track['artists'][0]['name']
		else:
			return_string = 'Could not find requested song'
		
		return close(intent_request['sessionAttributes'],
					'Fulfilled',
					{'contentType': 'PlainText',
					'content': return_string})
					
					
def validate_spotify(genre,startBpM,endBpM,duration,playlistName):
	
	return build_validation_result(True, None, None)
	
	#if searchKey is not None and searchKey not in searchKeys:
	if genre is None:
		return build_validation_result(False,
									   'genre',
									   'missing genre ')

	return build_validation_result(True, None, None)
	
	
def searchSpotify(intent_request):
	
	source = intent_request['invocationSource']
	
	genre = intent_request['currentIntent']['slots']['genre']
	startBpM = intent_request['currentIntent']['slots']['startBpM']
	endBpM = intent_request['currentIntent']['slots']['endBpM']
	duration = intent_request['currentIntent']['slots']['duration']
	playlistName = intent_request['currentIntent']['slots']['playlistName']
	token = intent_request['sessionAttributes']['general_key']
	
	#token='BQBebZ2K0Awc7D-ph4iaaRs7__U0_s8Do1xmHmj0N060AGe2fwPCCPvVEv4cBFnZTDv2C1uZrdrt1WOwQIOXOfPB2YW0DCQOLQzEfdgiUdNTRv9mfsb9NEUvprlwukxpN7shOVFrR6w6He-gsEw2SXcXZGylwyc0EW7rZhu2CDLGAma63lYK3ahowwzEy8w_qwSCr-UlhgdFAi-B2UA2WussIPGeqCW4WgyPUyVhNBZN0-s'
	
	
	'''
	results = spotify.search(q='genre:' + 'rock',type='track')
	print(results)
	source = intent_request['invocationSource']
	'''
	
	if source == 'DialogCodeHook':
		# Perform basic validation on the supplied input slots.
		# Use the elicitSlot dialog action to re-prompt for the first violation detected.
		slots = get_slots(intent_request)
	   
		validation_result =   validate_spotify(genre,startBpM,endBpM,duration,playlistName)
		if not validation_result['isValid']:
			slots[validation_result['violatedSlot']] = None
			return elicit_slot(intent_request['sessionAttributes'],
							  intent_request['currentIntent']['name'],
							  slots,
							  validation_result['violatedSlot'],
							  validation_result['message'])

		# Pass the price of the flowers back through session attributes to be used in various prompts defined
		# on the bot model.
		output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
		# if flower_type is not None:
		#     output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

		return delegate(output_session_attributes, get_slots(intent_request))
	
	if source == 'FulfillmentCodeHook':
		
		# genre = 'rock'
		# startBpM = 0
		# endBpM = 200
		# duration = 400000
		
		#playlist = selectPlayList(genre,startBpM, endBpM, duration,playlistName,token)
		#token = "BQA1DkQboo4POFHTgopdkW4oBHhgkJbvM-9GSNud8YgykYj-hGkHK1McRIKKlU2Ar4m1MFH4y-6DPpTxWvEma34y_YYBejQXghJawtzGXYFJU1_YJVMbGguZUy_UjbTKVyoanghiC5SMP2AO-EtNsG12jnpkskRh66VOZcw4OKHb5CC2lro25ddZTvw1Dnh5ag4WOg2W7qEtufcRNRxXW-K-n0YHRpKkSYCkwYuDUD3rsWs"
    
		sqs_response= post_details_to_queue(genre, startBpM, endBpM, duration,playlistName,token)
		print("sqs response", sqs_response)
	
		return close(intent_request['sessionAttributes'],
					'Fulfilled',
					{'contentType': 'PlainText',
					'content': 'Playlist Built'})
	
def post_details_to_queue(genre, startBpM, endBpM, duration,playlistName,token):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName='cloud_project_song_id.fifo')
    #song_id_list = ' '.join(s_id_list)
    response=queue.send_message(MessageBody='To be retrieved from dynamo', MessageAttributes={
    'genre': {
        'StringValue': genre,
        'DataType': 'String'
        },
    'startBpM': {
        'StringValue': str(startBpM),
        'DataType': 'String'
        },
    'endBpM': {
        'StringValue': str(endBpM),
        'DataType': 'String'
        },
    'duration': {
        'StringValue': str(duration),
        'DataType': 'String'
        },
    'playlistName': {
        'StringValue': playlistName,
        'DataType': 'String'
        },
    'token': {
        'StringValue': token,
        'DataType': 'String'
        }
    },
    MessageGroupId=''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]),
    MessageDeduplicationId=''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
    )    
    return "IDs posted"
    
def greeting(intent_request):
	source = intent_request['invocationSource']
	return close(intent_request['sessionAttributes'],
				 'Fulfilled',
				 {'contentType': 'PlainText',
				  'content': 'Hi! How may I help you?'})