from django.core.management.base import BaseCommand, CommandError

import sys
import logging
import json
import signal
from tweepy import Stream
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from twython import TwythonStreamer
from collect.models import Collection, Tweet
from django.conf import settings


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
                    try:
                        print "123123412341241234"
                        print status.id
                        data = status._json
                        print data
                        t, created = Tweet.objects.get_or_create(collection=collection,twitter_id=str(status.id))
                        t.data = data
                        logger.warn(str(t))
                        t.save()
                    except Exception:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            logger.error("Couldn't save a tweet: "+str(exc_obj))
                # if 'limit' in status:
                #     logger.warn("The filtered stream has matched more Tweets than its current rate limit allows it to be delivered.")
            def on_error(self, status):
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