import tweepy
import time
import pandas as pd

#API_KEY = "yIICoasw6pKiBI2AJy05gr5HW"
#API_KEY_SECRET = "BxgaODE9hzEGi2eBHX1oqKO1rYWivhluVtl9MIEk4nDtPdJNcA"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAM%2FobQEAAAAAx8iR67oOTfQsuZxX74hyyrl%2Btbc%3DIkH6l9Vb30RyavfzwzVteCPm0Hkwj31iAlLiLDRW8fOTZTSKdg" #original
#BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAPYXBAAAAAAACLXUNDekMxqa8h%2F40K4moUkGsoc%3DTYfbDKbT3jJPCEVnMYqilB28NHfOPqkca3qaAxGfsyKCs0wRbw"  #found online
#ACCESS_TOKEN = "2718271718-ER0qPpdIRcXu2VeHSbgH7KNKslq7cgpeDD10YFd"
#ACCESS_TOKEN_SECRET = "0QsDGgkHKuxOrSE0U3lsITVv5wojRBLnry1igUIIyV0Kc"

CLIENT = tweepy.Client(BEARER_TOKEN,wait_on_rate_limit=True)

#BC and AB wildfires
START_DATE = '2022-04-01T00:00:00Z' #april 1st 2022
END_DATE = '2022-11-01T00:00:00Z'   #november 1st 2022
# START_DATE = '2023-04-01T00:00:00Z' #april 1st 2023
# END_DATE = '2023-06-26T00:00:00Z' #june 27 2023
HASHTAGS = '(#BCwildfire OR #BCwildfires OR #BCfire OR #BCfires OR #ABWildfire OR #ABWildfires OR #ABFire OR #ABFires) lang:en -is:retweet -is:quote -is:reply'
#HASHTAGS = '(#BCincendies OR #ABincendies OR #ABfeu OR #BCfeu) lang:fr -is:retweet -is:quote -is:reply'

#ottawa storm 2022
# START_DATE = '2022-05-01T00:00:00Z'
# END_DATE = '2022-07-01T00:00:00Z'
# HASHTAGS = '(#OttawaStorm OR #OttawaOntarioCanada OR #ThunderStorm OR #Lightning OR #Weather OR #onstorm #rain OR #ottstorm OR #ottstorm2022 OR #ottawastorm2022) lang:en -is:retweet -is:quote -is:reply'

#NS wildfires 2023
# START_DATE = '2023-04-01T00:00:00Z'
# END_DATE = '2023-06-06T00:00:00Z'
# HASHTAGS = '(#wildfire OR #wildfires OR #nswildfire OR #wildfirens OR #wildfiresns OR #nsfire OR #nsfires OR #nswildfire2023 OR #wildfireseason OR #wildfiresmoke OR #wildfireprevention OR #wildfiresss OR #cawildfires OR #2023fireseason OR #fireemergencyns OR #helpnswildfires OR #firefightersns OR #nsfireresponse) lang:en -is:retweet -is:quote -is:reply'

#ottawa tornado 2018
# START_DATE = '2018-09-19T00:00:00Z'
# END_DATE = '2018-11-01T00:00:00Z'
# HASHTAGS = '(#ottnews OR #ottweather OR #ottstorm OR #tornado OR #ottawastorm OR #ottawatornado OR #ottcity) lang:en -is:retweet -is:quote -is:reply'

MAX_RESULTS = 200 #multiply by 50, will achieve around ___ tweets

def scrapeTweets(start_date, end_date, results, hashtags):
    tweets = []
    i = 0
    try:
        for response in tweepy.Paginator(CLIENT.search_all_tweets, 
                                query = hashtags,
                                user_fields = ['username', 'name', 'public_metrics', 'description', 'location','created_at','entities','id', 
                                                'pinned_tweet_id','profile_image_url','protected','url','verified','withheld'],
                                tweet_fields = ['created_at', 'geo', 'public_metrics', 'text','id', 'entities', 'lang'],
                                place_fields = ['country', 'country_code', 'full_name'],
                                media_fields = ['preview_image_url','url','public_metrics','duration_ms'],
                                expansions = ['author_id','geo.place_id','attachments.media_keys'],
                                start_time = start_date,
                                end_time = end_date,
                                #tweet_mode= 'extended',
                                max_results = 50):
            time.sleep(1)
            tweets.append(response)
            print(i)
            if i == results:
                break
            i+=1
        return tweets
    except:
        print('Error occured.')
        pass 

def populateDictionaries(response):
    # Take all of the users, and put them into a dictionary of dictionaries with the info we want to keep
    for user in response.includes['users']:
        user_dict[user.id] = {'username': user.username, 
                              'screen_name': user.name,
                              'followers': user.public_metrics['followers_count'],
                              'tweets': user.public_metrics['tweet_count'],
                              'description': user.description,
                              'location': user.location,
                              'created_at': user.created_at,
                              'entities': user.entities,
                              'id': user.id,
                              #'id_str': user.id_str,
                              'pinned_tweet_id': user.pinned_tweet_id,
                              'protected': user.protected,
                              'url': user.url,
                              'verified': user.verified,
                              'withheld': user.withheld}
    try:                         
        for place in response.includes['places']:
            place_dict[place.id] = {'country_code': place.country_code, 'full_name': place.full_name, 'country': place.country}
    except:
        pass     
    try:                         
        for media in response.includes['media']:
            media_dict[media.media_key] = {'preview_image_url': media.preview_image_url,'url':media.url,'public_metrics':media.public_metrics,'duration_ms':media.duration_ms}
    except:
        pass

    return user_dict, place_dict, media_dict

def makeDataframeFromTweets(tweet):
    # For each tweet, find the author's information
    author_info = user_dict[tweet.author_id]
    # Put all of the information we want to keep in a single dictionary for each tweet 
    d ={'tweet_id': tweet.id,
        #'author_id': tweet.author_id, 
        'username': author_info['username'],
        #'author_followers': author_info['followers'],
        #'author_tweets': author_info['tweets'],
        #'author_description': author_info['description'],
        'author_location': author_info['location'],
        'text': tweet.text,
        'lang': tweet.lang,
        'created_at': tweet.created_at,
        #'retweets': tweet.public_metrics['retweet_count'],
        #'replies': tweet.public_metrics['reply_count'],
        #'likes': tweet.public_metrics['like_count'],
        #'quote_count': tweet.public_metrics['quote_count']
        }

    if tweet.geo:
        try:
            d['country_code'] = place_dict[tweet.geo['place_id']]['country_code']
        except:
            d['country_code'] = ''
        try:
            d['country'] = place_dict[tweet.geo['place_id']]['country']
        except:
            d['country'] = ''
        try:
            d['full_name'] = place_dict[tweet.geo['place_id']]['full_name']
        except:
            d['full_name'] = ''         
    else:
        d['country_code'] = ''
        d['country'] = ''
        d['full_name'] = ''

    # d['preview_image_url']='' 
    d['url'] = ''
    # d['public_metrics']=''
    # d['duration_ms']=''

    if tweet.attachments:
        # try:
        #    for media_key in tweet.attachments['media_keys']:
        #        d['preview_image_url']=d['preview_image_url'] +'\t' + media_dict[media_key]['preview_image_url']
        # except:
        #   d['preview_image_url']=''
        try:
            for media_key in tweet.attachments['media_keys']:
                d['url'] = d['url'] + '\t'+ media_dict[media_key]['url']
        except:
            d['url'] = ''
        # try:
        #     for media_key in tweet.attachments['media_keys']:
        #         d['public_metrics']= d['public_metrics'] +'\t' +media_dict[media_key]['public_metrics']
        # except:
        #     d['public_metrics']=''
        # try:
        #     for media_key in tweet.attachments['media_keys']:
        #         d['duration_ms']=d['duration_ms'] + '\t' + media_dict[media_key]['duration_ms']
        # except:
        #     d['duration_ms']=''

    # try:
    #     #print('TWEET.ENTITIES:', tweet.entities)
        
    #     if 'urls' in tweet.entities:
    #         d['urls'] = tweet.entities['urls']
    #     else:
    #         d['urls'] = []
        
    #     if 'hashtags' in tweet.entities:
    #         d['hashtags'] = tweet.entities['hashtags']
    #     else:
    #         d['hashtags'] = []     
    # except:
    #     d['urls'] = []      
    #     d['hashtags'] = []          
    
    result.append(d)

tweets = scrapeTweets(START_DATE, END_DATE, MAX_RESULTS, HASHTAGS)
user_dict = {}
place_dict = {}
media_dict = {}
result = []
ctr=0
# Loop through each response object
for response in tweets:
    #print('RESPONSE:', response)
    ctr+=1
    user_dict, place_dict, media_dict = populateDictionaries(response)

    for tweet in response.data:
        makeDataframeFromTweets(tweet)

# convert this list of dictionaries into a dataframe
df = pd.DataFrame(result)
df.to_csv ('twitter_BC_AB_wildfires_apr-nov2022_2,193.csv', index = None, header=True)