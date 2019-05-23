import tweepy
import re
import matplotlib.pyplot as plt
import json
import os
from textblob_de import TextBlobDE as TextBlob
from config import *

SENTIWS_POS_PATH = "SentiWS/SentiWS_v2.0_Positive.txt"
SENTIWS_NEG_PATH = "SentiWS/SentiWS_v2.0_Negative.txt"

def prepare_sentiws():
    sentiment = dict()    
    regex = r"(\w+)\|(\w+)\s(\S+)\s(\S*)"
    
    for fp in [SENTIWS_POS_PATH, SENTIWS_NEG_PATH]:
        with open(fp) as f:
            for line in f.readlines():
                matches = re.findall(regex, line)[0]
                score = float(matches[2])
                sentiment[matches[0].lower()] = score
                for inf in matches[3].split(','):
                    sentiment[inf.lower()] = score
    
    return sentiment



def plot_sentiment():
    scores = [analyzer.polarity_scores(tweet)['compound'] for tweet in list(set(tweet_text))]
    plt.hist(scores, bins=20)

def main():
    sentiment_scores = prepare_sentiws()

    # Authorization and call api
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    api.rate_limit_status

    rate_limit_status = api.rate_limit_status()
    search_limit = rate_limit_status['resources']['search']['/search/tweets']

    print("Rate Limit: {} searches remaining".format(search_limit['remaining']))
    
    woeid = -1
    for country in api.trends_available():
        if country["name"] == "Germany":
            woeid = country["woeid"]
            break
    
    if woeid == -1:
        print("Country not found")
        quit()

    trends = api.trends_place(woeid)
    topics = list()
    for trend in trends[0]["trends"]:
        topics.append(trend["name"])

    cleanup_regex = r"\#|[^\sa-zA-ZäöüÄÖÜß]|\d|\n\n|\s{2,}|http[s]([^\s]+)"
    
    if os.path.isfile("cache.json"):
        with open("cache.json", "r") as f:
            topic_data = json.load(f)
    else:
        topic_data = dict()
        for topic in topics:
            print("Gathering tweets for topic {}".format(topic))
            topic_data[topic] = {
                "tweets": []
            }
            tweets = [status for status in tweepy.Cursor(api.search, q=topic, result_type="recent", tweet_mode="extended", lang="de", wait_on_rate_limit=True).items(50)]
            for tweet in tweets:
                tweet = tweet._json
                if 'retweeted_status' in tweet:
                    raw_tweet = tweet['retweeted_status']['full_text']
                else:
                    raw_tweet = tweet['full_text']

                result = re.sub(cleanup_regex, "", raw_tweet, 0)
                
                topic_data[topic]["tweets"].append(result)

        with open("cache.json", "w+") as f:
            json.dump(topic_data, f)

    global_score = 0

    for topic in topic_data:
        tokens = list()
        for token in result.split():
            if not token in tokens:
                tokens.append(token)

        print("Topic: {}".format(topic))
        score = 0
        found = 0
        for t in tokens:
            if t.lower() in sentiment_scores:
                score += sentiment_scores[t.lower()]
                found += 1
        #global_score += score
        print("Total Score: {}".format(score))
        print("Tokens in dictionary: {}/{}".format(found, len(tokens)))
        if found > 0:
            print("Relative Score: {:.4f}".format(score/found))
            global_score += score/found

        tb = TextBlob(" ".join(topic["tweets"]))
        print(tb.sentiment)
        print()

    print("Global Score: {}".format(global_score))
    print("Global rel: {:.4f}".format(global_score/len(tokens)))
        


    """
    # Get tweets using Tweepy api search
    max_tweets=1000
    tweets = [status for status in tweepy.Cursor(api.setweepy rate limith, 
                                                q="Worltweepy rate limitup", 
                                                result_tweepy rate limite="recent", 
                                                tweet_mtweepy rate limit="extended",
                                                lang="dtweepy rate limit
                                                ).items(max_tweets)]
    # parse tweet text
    tweet_text = []
    for tweet in tweets:
        tweet = tweet._json
        if 'retweeted_status' in tweet:
            tweet_text.append(tweet['retweeted_status']['full_text'])
        else:
            tweet_text.append(tweet['full_text'])
    """

if __name__ == '__main__':
    main()
