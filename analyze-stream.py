import tweepy
import re
import json
import os
import time
from textblob_de import TextBlobDE as TextBlob
from .env import *
from http.client import IncompleteRead # Python 3

class MyStreamListener(tweepy.StreamListener):
    cleanup_regex = r"\#|[^\sa-zA-ZäöüÄÖÜß]|\d|\n\n|\s{2,}|http[s]([^\s]+)"
    tweet_buffer = list()
    buffer_len = 1000
    tweet_count = 0
    time_start = time.time()

    def on_status(self, status):
        print("[Status] %s" % status.text)

    def on_error(self, status):
        print("[Error] %s" % status)

    def on_data(self, data):
        json_data = json.loads(data)
        self.process_tweet(json_data)
        return True

    def process_tweet(self, tweet):
        raw_text = tweet["text"]
        text = re.sub(self.cleanup_regex, "", raw_text, 0)
        print("[Tweet] %s" % text)
        tb = TextBlob(" ".join(self.tweet_buffer))
        print(tb.sentiment.polarity)
        self.tweet_buffer.append(text)
        self.tweet_buffer = self.tweet_buffer[-1 * self.buffer_len:]
        self.tweet_count += 1
        if self.tweet_count % 100 == 0:
            print("[Status] Tweet count: {}".format(self.tweet_count))
            print("[Status] Tweets per second: {:.2}".format(self.tweet_count/(time.time() - self.time_start)))
            tb = TextBlob(" ".join(self.tweet_buffer))
            print("Sentiment last {} tweets: {:.5}".format(self.buffer_len, tb.sentiment.polarity))
            #with open("/var/www/scripts/sentiment.txt", "w+") as f:
            #    f.write("{}\n".format(tb.sentiment.polarity * 50 + 50))


def tweepy_connect():
    # Authorization and call api
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    return api
    
def get_trending_topics(api, country_name=None):
    if country_name:
        woeid = -1
        for country in api.trends_available():
            if country["name"] == country_name:
                woeid = country["woeid"]
                break
        
        if woeid == -1:
            print("Country not found")
            quit()

    trends = api.trends_place(woeid)
    topics = list()
    for trend in trends[0]["trends"]:
        topics.append(trend["name"])
    
    return topics

def main():
    api = tweepy_connect()

    myStreamListener = MyStreamListener()

    while True:
        try:
            topics = get_trending_topics(api, "Germany")
            myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
            myStream.filter(track=topics)
        except IncompleteRead:
            # Oh well, reconnect and keep trucking
            continue
        except KeyboardInterrupt:
            # Or however you want to exit this loop
            myStream.disconnect()
            break
   

if __name__ == '__main__':
    main()
