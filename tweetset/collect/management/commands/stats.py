from django.core.management.base import BaseCommand, CommandError

import sys
import logging
import signal
from collect.models import Collection, Tweet
from django.conf import settings
import operator
import json
from nltk import bigrams
from collections import Counter
import re
from collections import defaultdict
from nltk.corpus import stopwords
import string
import vincent
import arrow
from time import sleep

class Command(BaseCommand):
    args = 'collection_id'
    help = 'Analyze tweets'

    def handle(self, *args, **options):
        if (len(args)<1):
            raise CommandError('Arguments "collection_id" is required!')

        def exit_gracefully(signal, frame):
            sys.exit(0)

        signal.signal(signal.SIGINT, exit_gracefully)
        signal.signal(signal.SIGTERM, exit_gracefully)

        collection = Collection.objects.get(pk=args[0])
        print collection.id

        # t1 = 'germania'
        # t2 = 'italia'
        # dates_t1= []
        # dates_t2 = []

        path_to_json = settings.STATICFILES_DIRS[0] + 'json/'
        # c = get_object_or_404(Collection, pk=collection_id, user=request.user)

        list_of_tweets = []
        for t in collection.tweets.all():
            list_of_tweets.append(t.data)
        
        # print list_of_tweets

        start = arrow.now()

        punctuation = list(string.punctuation)
        stop = stopwords.words('spanish') + stopwords.words('french') + stopwords.words('german') + stopwords.words('italian') + stopwords.words('english') + punctuation + ["I'm", "don't", "i'm", "Don't", "l'a", "amp", "ter", "les", "c'est", 'de', 'en', 'el', 'https', 'rt', 'via', 'RT']

        print stop
        emoticons_str = r"""
            (?:
                [:=;]  # Eyes
                [oO\-]?  # Nose (optional)
                [D\)\]\(\]/\\OpP]  # Mouth
            )"""

        regex_str = [
            emoticons_str,
            r'<[^>]+>',  # HTML tags
            r'(?:@[\w_]+)',  # @-mentions
            r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
            r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',

            r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
            r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
            r'(?:[\w_]+)',  # other words
            r'(?:\S)'  # anything else
        ]

        tokens_re = re.compile(r'('+'|'.join(regex_str)+')',
                               re.VERBOSE | re.IGNORECASE)
        emoticon_re = re.compile(r'^'+emoticons_str+'$',
                                 re.VERBOSE | re.IGNORECASE)


        def tokenize(s):
            return tokens_re.findall(s)


        def preprocess(s, lowercase=True):
            tokens = tokenize(s)
            if lowercase:
                tokens = [token if emoticon_re.search(token)
                          else token.lower() for token in tokens]
            return tokens


        pr = 0
        err = 0
        a = 0

        geo_data = {
                "type": "FeatureCollection",
                "features": []
            }


        count_stop = Counter()
        count_hashtags = Counter()
        count_mentions = Counter()
        count_bigram = Counter()
        for t in list_of_tweets:
            tweet = t
            try:
                pr += 1
                print str(tweet['created_at']) + " ok: " + str(pr)
                terms_stop = [term for term in preprocess(tweet['text'])
                              if term not in stop and
                              not term.startswith(('#', '@', 'http')) and
                              len(term) > 2]
                hashtags_only = [term for term in preprocess(tweet['text'])
                                 if term.startswith(('#')) and
                                len(term) > 2]
                mentions_only = [term for term in preprocess(tweet['text'])
                                 if term.startswith(('@')) and len(term) > 1]
                # terms = [term for term in preprocess(tweet['text'])
                #          if term not in stop and len(term) != 1]
                # # track when the hashtag is mentioned
                # if t1 in terms:
                #     dates_t1.append(tweet['created_at'])
                # if t2 in terms:
                #     dates_t2.append(tweet['created_at'])
            except:
                err += 1
            count_stop.update(terms_stop)
            count_hashtags.update(hashtags_only)
            count_mentions.update(mentions_only)

            print "map: ",
            print a
            a += 1
            try:
                if tweet['coordinates']:
                    geo_json_feature = {
                        "type": "Feature",
                        "geometry": tweet['coordinates'],
                        "properties": {
                            "text": tweet['text'],
                            "created_at": tweet['created_at']
                        }
                    }
                    geo_data['features'].append(geo_json_feature)
            except: 
                pass

            # asjdnalsjkdalsd
            # askdjbaskjdhajkhsd
            # if pr == 1000:
            #     break

        nElements = 20

        print "----------------------------"

        print "generating most common terms json"

        word_freq = count_stop.most_common(nElements)
        labels, freq = zip(*word_freq)
        data = {'data': freq, 'x': labels}
        bar = vincent.Bar(data, iter_idx='x', height=400, width=600)
        bar.x_axis_properties(label_angle=-45, label_align="right")
        bar.legend(title="Most frequent terms")
        bar.to_json(path_to_json + str(collection.id) + '_freq_terms.json')

        print "generating most common hashtags json"

        word_freq = count_hashtags.most_common(nElements)
        labels, freq = zip(*word_freq)
        data = {'data': freq, 'x': labels}
        bar = vincent.Bar(data, iter_idx='x', height=400, width=600)
        bar.x_axis_properties(label_angle=-45, label_align="right")
        bar.legend(title="Most frequent hashtags")
        bar.to_json(path_to_json + str(collection.id) + '_freq_hashtags.json')

        print "generating most common mentions json"

        word_freq = count_mentions.most_common(nElements)
        labels, freq = zip(*word_freq)
        data = {'data': freq, 'x': labels}
        bar = vincent.Bar(data, iter_idx='x', height=400, width=600)
        bar.x_axis_properties(label_angle=-45, label_align="right")
        bar.legend(title="Most frequent mentions")
        bar.to_json(path_to_json + str(collection.id) + '_freq_mentions.json')


        # Save geo data
        with open(path_to_json + str(collection.id) + '_map.json', 'w') as fout:
            fout.write(json.dumps(geo_data, indent=4))



        # print "time charting now"

        # # 1 time charting
        # print dates_t1

        # print 'asdasdasdasdasdasdadsasd'
        # sleep(3)

        # ones = [1]*len(dates_t1)
        # twos = [1]*len(dates_t2)


        # # 2 the index of the series
        # print '2'

        # idxn = pandas.DatetimeIndex(dates_t1)
        # idxp = pandas.DatetimeIndex(dates_t2)



        # # 3 the actual series (at series of 1s for the moment)
        # print '3'

        # t1 = pandas.Series(ones, index=idxn)
        # t2 = pandas.Series(twos, index=idxp)



        # # 4 Resampling / bucketing
        # print '4'
        # per_minute_t1 = t1.resample('1Min', how='sum').fillna(0)
        # per_minute_t2 = t2.resample('1Min', how='sum').fillna(0)


        # # 5 all the data together
        # print '5'

        # match_data = dict(t1=per_minute_t1, t2=per_minute_t2)
        # # 6 we need a DataFrame, to accommodate multiple series


        # print '6'
        # all_matches = pandas.DataFrame(data=match_data,
        #                                index=per_minute_t1.index)
        # # 7 Resampling as above
        # print '7'
        # all_matches = all_matches.resample('1Min', how='sum').fillna(0)
        # # 8 and now the plotting
        # print '8'
        # boh = [t1, t2]
        # time_chart = vincent.Line(all_matches[['germania', 'italia']])
        # time_chart.axis_titles(x='Time', y='Freq')
        # tit = t1 + ' vs ' + t2
        # time_chart.legend(title=tit)
        # time_chart.to_json(path_to_json + str(collection.id) + '_time.json', 'w')

        # print "started at: " + str(start)
        # print ''

        # stop = arrow.now()
        # print "stopped at: " + str(stop)

        # print ''

        # print "total time: " + str(stop - start)

      