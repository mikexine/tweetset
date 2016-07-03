from django.core.management.base import BaseCommand, CommandError

import sys
import logging
import json
import signal
from tweepy import Stream
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from twython import TwythonStreamer
from collect.models import Collection, Tweet, TweetAccount
from django.conf import settings
import datetime


class Command(BaseCommand):
    args = 'collection_id'
    help = 'Collects tweets from the Twitter stream to the database.'

    def handle(self, *args, **options):
        if (len(args)<1):
            raise CommandError('Arguments "collection_id" is required!')

        FORMAT = '[%(asctime)-15s] %(levelname)s: %(message)s'

        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger('twitter')

        def exit_gracefully(signal, frame):
            logger.warn("Shutdown signal received! Shutting down.")
            sys.exit(0)

        signal.signal(signal.SIGINT, exit_gracefully)
        signal.signal(signal.SIGTERM, exit_gracefully)

        collection = Collection.objects.get(pk=args[0])

        class MyListener(StreamListener):
            def on_status(self, status):
                if status.text is not None:
                    # try:
                        # data = status._json
                        print '123\n\n'
                        print status.user 
                        print '123\n\n'
                        usr, cr = TweetAccount.objects.update_or_create(
                            account_id=status.user.id,
                            followers_count=status.user.followers_count,
                            following_count=status.user.friends_count,
                            screen_name=status.user.screen_name,
                            verified=status.user.verified,
                            profile_image_url=status.user.profile_image_url)

                        print '1'
                        print usr
                        t, created = Tweet.objects.get_or_create(collection=collection,twitter_user = usr,twitter_id=int(status.id))
                        # t.data = data
                        t.text = status.text
                        if status.coordinates is not None:
                            t.lon = status.coordinates['coordinates'][0]
                            t.lat = status.coordinates['coordinates'][1]
                        else:
                            t.lon = None
                            t.lat = None
                        t.tweet_time = status.created_at
                        logger.warn(str(t))

                        if status.entities['hashtags'] == []:
                            t.hashtags = None
                        else:
                            h = []
                            for hashtag in range(len(status.entities['hashtags'])):
                                h.append(status.entities['hashtags'][hashtag]['text'])
                            t.hashtags = h


                        if status.entities['urls'] == []:
                            t.urls = None
                        else:
                            h = []
                            for url in range(len(status.entities['urls'])):
                                h.append(status.entities['urls'][url]['display_url'])
                            t.urls = h


                        if status.entities['user_mentions'] == []:
                            t.urls = None
                        else:
                            h = []
                            for user in range(len(status.entities['user_mentions'])):
                                h.append(status.entities['user_mentions'][user]['screen_name'])
                            t.user_mentions = h


                        t.in_reply_to_user = status.in_reply_to_screen_name
                        t.lang = status.lang



                        t.save()
                    # except Exception:
                    #         exc_type, exc_obj, exc_tb = sys.exc_info()
                    #         logger.error("Couldn't save a tweet: "+str(exc_obj))
                # if 'limit' in status:
                #     logger.warn("The filtered stream has matched more Tweets than its current rate limit allows it to be delivered.")
            def on_error(self, status):
                print "Received error code "+str(status)+"."
                logger.error("Received error code "+str(status)+".")

        # class TapStreamer(TwythonStreamer):
        #     def on_success(self, data):
        #         if 'text' in data:
        #             try:
        #                 t, created = Tweet.objects.get_or_create(collection=collection,twitter_id=str(data['id']))
        #                 t.data = data
        #                 t.save()
        #             except Exception:
        #                 exc_type, exc_obj, exc_tb = sys.exc_info()
        #                 logger.error("Couldn't save a tweet: "+str(exc_obj))
        #         if 'limit' in data:
        #             logger.warn("The filtered stream has matched more Tweets than its current rate limit allows it to be delivered.")
        #     def on_error(self, status_code, data):
        #         logger.error("Received error code "+str(status_code)+".")

        social_auth = collection.user.social_auth.get(provider='twitter')

        # stream = TapStreamer(settings.SOCIAL_AUTH_TWITTER_KEY, settings.SOCIAL_AUTH_TWITTER_SECRET, social_auth.tokens['oauth_token'], social_auth.tokens['oauth_token_secret'])

        auth = OAuthHandler(settings.SOCIAL_AUTH_TWITTER_KEY, settings.SOCIAL_AUTH_TWITTER_SECRET)
        auth.set_access_token(social_auth.tokens['oauth_token'], social_auth.tokens['oauth_token_secret'])

        logger.info("Collecting tweets from the streaming API...")
        twitter_stream = Stream(auth, MyListener())
        if collection.follow or collection.track or collection.locations:
            # stream.statuses.filter(follow=collection.follow,track=collection.track,locations=collection.locations)
            twitter_stream.filter(follow=collection.follow,track=collection.track,locations=collection.locations)
        else:
            # stream.statuses.sample()
            pass