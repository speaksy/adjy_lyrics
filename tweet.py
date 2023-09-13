from requests_oauthlib import OAuth1Session
import os
import json
import stat

# In your terminal please set your environment variables by running the following lines of code.
# export 'CONSUMER_KEY'='<your_consumer_key>'
# export 'CONSUMER_SECRET'='<your_consumer_secret>'

def generate_oath_access_token(consumer_key, consumer_secret):
  # Based on boilerplate from 
  # https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/Manage-Tweets/create_tweet.py
  
  # Get request token
  request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
  oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

  try:
      fetch_response = oauth.fetch_request_token(request_token_url)
  except ValueError:
      print(
          "There may have been an issue with the consumer_key or consumer_secret you entered."
      )

  resource_owner_key = fetch_response.get("oauth_token")
  resource_owner_secret = fetch_response.get("oauth_token_secret")
  print("Got OAuth token: %s" % resource_owner_key)

  # Get authorization
  base_authorization_url = "https://api.twitter.com/oauth/authorize"
  authorization_url = oauth.authorization_url(base_authorization_url)
  print("Please go here and authorize: %s" % authorization_url)
  verifier = input("Paste the PIN here: ")

  # Get the access token
  access_token_url = "https://api.twitter.com/oauth/access_token"
  oauth = OAuth1Session(
      consumer_key,
      client_secret=consumer_secret,
      resource_owner_key=resource_owner_key,
      resource_owner_secret=resource_owner_secret,
      verifier=verifier,
  )
  oauth_tokens = oauth.fetch_access_token(access_token_url)

  access_token = oauth_tokens["oauth_token"]
  access_token_secret = oauth_tokens["oauth_token_secret"]

  return access_token, access_token_secret

def get_oath_access_token(consumer_key, consumer_secret):
  secret_file = r'access_token.txt'
  access_token, access_token_secret = None, None
  if not os.path.exists(secret_file):
    access_token, access_token_secret = generate_oath_access_token(consumer_key, consumer_secret)
    with open(secret_file, 'w') as f:
        f.write(access_token)
        f.write('\n')
        f.write(access_token_secret)
  else:
    with open(secret_file, 'r') as f:
        access_token = f.readline().strip()
        access_token_secret = f.readline().strip()
  return access_token, access_token_secret

def post(text: str, image_path: str):
  # Get an oauth session
  consumer_key = os.environ.get("CONSUMER_KEY")
  consumer_secret = os.environ.get("CONSUMER_SECRET")
  access_token, access_token_secret = get_oath_access_token(consumer_key, consumer_secret)
  oauth = OAuth1Session(
      consumer_key,
      client_secret=consumer_secret,
      resource_owner_key=access_token,
      resource_owner_secret=access_token_secret,
  )

  # Upload some media
  # Load media
  media_size = os.path.getsize(image_path)
  assert(media_size <= 1e6)
  media_bytes = None
  with open(image_path, 'rb') as file:
    media_bytes = file.read()
  
  print(f'image size: {media_size} bytes')

  # INIT
  init_payload = {
      'command': 'INIT',
      'total_bytes': media_size,
      'media_type': 'image/png',
      'media_category': 'tweet_image',
   }
  init_response = oauth.post(
      'https://upload.twitter.com/1.1/media/upload.json',
      headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
      params=init_payload, 
  )
  print(init_response)
  media_id = init_response.json()['media_id_string']

  # APPEND
  append_payload = {
      'command': 'APPEND',
      'media_id': media_id,
      'segment_index': '0',
  }
  append_response = oauth.post(
      'https://upload.twitter.com/1.1/media/upload.json',
    #   headers={ 'Content-Type': 'multipart/form-data' },
      files={ 'media': media_bytes },
      params=append_payload, 
  )

  # FINALIZE
  finalize_payload = {
      'command': 'FINALIZE',
      'media_id': media_id
    }
  finalize_response = oauth.post(
      "https://upload.twitter.com/1.1/media/upload.json",
      headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
      params=finalize_payload,
  )

  # Make the tweet
  tweet_payload = {
      'text': text,
      'media': { 'media_ids' : [ media_id ] }
    }
  tweet_response = oauth.post(
      "https://api.twitter.com/2/tweets",
      json=tweet_payload,
  )

  if tweet_response.status_code != 201:
      raise Exception(
          "Request returned an error: {} {}".format(tweet_response.status_code, tweet_response.text)
      )

  print("Tweet response code: {}".format(tweet_response.status_code))

  # Save the response as JSON
  json_response = tweet_response.json()
  print(json.dumps(json_response, indent=4, sort_keys=True))

if __name__ == '__main__':
  # Sends a test tweet

  # Get an oath session
  consumer_key = os.environ.get("CONSUMER_KEY")
  consumer_secret = os.environ.get("CONSUMER_SECRET")
  print(consumer_key)
  access_token, access_token_secret = get_oath_access_token(consumer_key, consumer_secret)
  print(access_token)
  print(access_token_secret)
  oauth = OAuth1Session(
      consumer_key,
      client_secret=consumer_secret,
      resource_owner_key=access_token,
      resource_owner_secret=access_token_secret,
  )

  # Upload some media
  # Load media
  test_media_path = r'test_media.png'
  stat_info = os.stat(test_media_path)
  media_size = stat_info[stat.ST_SIZE]
  assert(media_size <= 1e6)
  media_bytes = None
  with open(test_media_path, 'rb') as file:
    media_bytes = file.read()
#   print(media_bytes)
  print(f'media size: {media_size} bytes')

  # INIT
  init_payload = {
      'command': 'INIT',
      'total_bytes': media_size,
      'media_type': 'image/png',
      'media_category': 'tweet_image',
   }
  init_response = oauth.post(
      'https://upload.twitter.com/1.1/media/upload.json',
      headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
      params=init_payload, 
  )
  print('init', init_response, json.dumps(init_response.json()))
  media_id = init_response.json()['media_id_string']
  print(f'media_id = {media_id}')

  # APPEND
  append_payload = {
      'command': 'APPEND',
      'media_id': media_id,
      'segment_index': '0',
  }
  append_response = oauth.post(
      'https://upload.twitter.com/1.1/media/upload.json',
    #   headers={ 'Content-Type': 'multipart/form-data' },
      files={ 'media': media_bytes },
      params=append_payload, 
  )
  print('append', append_response)

  # FINALIZE
  finalize_payload = {
      'command': 'FINALIZE',
      'media_id': media_id
    }
  finalize_response = oauth.post(
      "https://upload.twitter.com/1.1/media/upload.json",
      headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
      params=finalize_payload,
  )
  print('finalize', finalize_response, json.dumps(finalize_response.json()))

  # Make the tweet
  tweet_payload = {
      'text': 'this is a test tweet that should have an image attached',
      'media': { 'media_ids' : [ media_id ] }
    }
  tweet_response = oauth.post(
      "https://api.twitter.com/2/tweets",
      json=tweet_payload,
  )

  if tweet_response.status_code != 201:
      raise Exception(
          "Request returned an error: {} {}".format(tweet_response.status_code, tweet_response.text)
      )

  print("Response code: {}".format(tweet_response.status_code))

  # Save the response as JSON
  json_response = tweet_response.json()
  print(json.dumps(json_response, indent=4, sort_keys=True))
