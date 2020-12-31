import tweepy
import subprocess
import requests
import time
import os,sys
import urllib.request, urllib.error, urllib.parse
import math
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

from sendEmail import sendEmail, sendErrorEmail
from timelapse import getCanonicalUrl
from getConfig import getConfigParameters

from common import getFormattedTagURL
from common import isPosted
from common import getPostDateTime
from common import getPageTitle
from common import datetime_from_utc_to_local

# Consumer keys and access tokens, used for OAuth
consumer_key = getConfigParameters('twitterConsumerKey')
consumer_secret = getConfigParameters('twitterConsumerSecret')
access_token = getConfigParameters('twitterAccessToken')
access_token_secret = getConfigParameters('twitterAccessTokenSecret')


# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Creation of the actual interface, using authentication
api = tweepy.API(auth)


whatDidItLookLikeTwitterScreenName = getConfigParameters('whatDidItLookLikeTwitterScreenName')
whatDidItLookLikeTwitterRequestHashtag = getConfigParameters('whatDidItLookLikeTwitterRequestHashtag')

globalBlogName = getConfigParameters('globalBlogName')
globalPrefix = getConfigParameters('globalPrefix')

nominationDifferentialFileName = globalPrefix + 'nominationDifferential.txt'
globalRequestFilename = globalPrefix + 'twitter_requests_wdill.txt'
sinceIDFilename = globalPrefix + 'timelapseTwitterSinceIDFile.txt'
tumblrDataFileName = globalPrefix + 'tumblrUrlsDataFile.txt'
#<url, [tweet_id, created_at_datetime]>

globalDictionaryOfTweetExtraInformation = {}

def expandUrl(url):
    if(len(url) > 0):
        url = url.strip()
        #http://stackoverflow.com/questions/17910493/complete-urls-in-tweepy-when-expanded-url-is-not-enough-integration-with-urllib
        '''
        try:
            url = urlparse(url)    # split URL into components
            conn = http.client.HTTPConnection(url.hostname, url.port)
            conn.request('HEAD', url.path)            # just look at the headers
            rsp = conn.getresponse()
            if rsp.status in (301,401):               # resource moved (permanent|temporary)
                return rsp.getheader('location')
            else:
                return url
            conn.close()
        except:
            return ''
        '''
        return requests.get(url).url

    else:
        return ''


#syntax for request is "screen_name #hashtag url1 url2...urln"
def checkForRequestTweetSignature(tweet):
    if(len(tweet) > 0):
        #is tweet addressed to whatDidItLookLikeTwitterScreenName: old logic
        '''
        indexOfScreenName = tweet.find(whatDidItLookLikeTwitterScreenName)
        indexOfRequestHashtag = tweet.find(whatDidItLookLikeTwitterRequestHashtag)

        if(indexOfScreenName > -1 and indexOfRequestHashtag > -1 and indexOfScreenName < indexOfRequestHashtag):
            #extract url from text
            return tweet[indexOfRequestHashtag + len(whatDidItLookLikeTwitterRequestHashtag):].split(',')
        else:
            return ''
        '''

        indexOfRequestHashtag = tweet.find(whatDidItLookLikeTwitterRequestHashtag)
        if(indexOfRequestHashtag > -1):
            #extract url from text
            return tweet[indexOfRequestHashtag + len(whatDidItLookLikeTwitterRequestHashtag):].split(',')
        else:
            return ''
    else:
        return ''

#gets tweets with since id larger (means tweet is newer) than the previous since id 
#updates since id with largest tweet sinceID
def getRequestUrls():


    try:
        sinceIDFile = open(sinceIDFilename, 'r')
        line = sinceIDFile.readline()

        if(len(line) > 1):
            sinceIDValue = int(line)
        else:
            sinceIDValue = int('0')

        sinceIDFile.close()
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print((fname, exc_tb.tb_lineno, sys.exc_info() ))
        sinceIDValue = int('0')
        sinceIDFile.close()


    requestsRemaining = api.rate_limit_status()['resources']['search']['/search/tweets']['remaining']
    #requestsRemaining = 10
    print("Before Request remaining: ", requestsRemaining)

    if( requestsRemaining > 0 ):
        #<user, expandedUrlsArray>
        expandedUrlsDictionary = {}


        #assume initially tweet is present
        isTweetPresentFlag = True
        while( isTweetPresentFlag ):
            
            #if tweet is present this will change the False to True, else it will remain False and Stop the loop
            isTweetPresentFlag = False
            print("sinceIDValue: ", sinceIDValue)
            for tweet in tweepy.Cursor(api.search, q="%23whatdiditlooklike", since_id=sinceIDValue).items(30):
                isTweetPresentFlag = True
                #print "tweet_id:", tweet.id, ",", tweet.user.screen_name, " - ", tweet.text ,", ", tweet.created_at
                #tweet time is in UTC, so convert to local
                localTimeTweet = datetime_from_utc_to_local(tweet.created_at)
                #now = datetime.now()
                #delta = now - localTimeTweet

                #update since_id
                if( tweet.id > sinceIDValue ):
                    sinceIDValue = tweet.id

                print(localTimeTweet, ",tweet_id:", tweet.id, ",", tweet.user.screen_name, " - ", tweet.text)
                print("")

                shortTwitterUrls = checkForRequestTweetSignature(tweet.text)
                #print "NEW TWEET TODAY, from: ", tweet.user.screen_name
                print(shortTwitterUrls)
                if(len(shortTwitterUrls) > 0):
                    for url in shortTwitterUrls:
                        potentialExpandedUrl = expandUrl(url)

                        #url normalization - start
                        #if( potentialExpandedUrl[-1] == '/' ):
                        #    potentialExpandedUrl = potentialExpandedUrl[:-1]
                        #url normalization - end

                        if(len(potentialExpandedUrl) > 0):

                            #create new entry for user since user is not in dictionary
                            potentialExpandedUrl = potentialExpandedUrl.strip()
                            if( tweet.user.screen_name in expandedUrlsDictionary):
                                expandedUrlsDictionary[tweet.user.screen_name].append(potentialExpandedUrl)
                            else:
                                expandedUrlsDictionary[tweet.user.screen_name] = [potentialExpandedUrl]

                            #add the created_at date for this tweet
                            globalDictionaryOfTweetExtraInformation[potentialExpandedUrl] = [tweet.id, localTimeTweet]

            
            if( isTweetPresentFlag ):
                print('...sleeping for 15 seconds')
                time.sleep(15)
                


    try:
        sinceIDFile = open(sinceIDFilename, 'w')
        sinceIDFile.write(str(sinceIDValue) + '\n')
        sinceIDFile.close()
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print((fname, exc_tb.tb_lineno, sys.exc_info() ))
        sinceIDFile.close()

    print("expandedUrlsDictionary: ", expandedUrlsDictionary)
    return expandedUrlsDictionary

def getRequestUrls_old(differenceInDaysCoefficient = 0):

    #<user, expandedUrlsArray>
    expandedUrlsDictionary = {}

    for tweet in list(tweepy.Cursor(api.search, q="%23whatdiditlooklike").items()):

        #print "tweet_id:", tweet.id, ",", tweet.user.screen_name, " - ", tweet.text ,", ", tweet.created_at
        #tweet time is in UTC, so convert to local
        localTimeTweet = datetime_from_utc_to_local(tweet.created_at)
        now = datetime.now()

        delta = now - localTimeTweet

        if( delta.days <= differenceInDaysCoefficient ):
            #print localTimeTweet, ",tweet_id:", tweet.id, ",", tweet.user.screen_name, " - ", tweet.text
            shortTwitterUrls = checkForRequestTweetSignature(tweet.text)
            #print "NEW TWEET TODAY, from: ", tweet.user.screen_name

            if(len(shortTwitterUrls) > 0):
                for url in shortTwitterUrls:
                    potentialExpandedUrl = expandUrl(url)
                    if(len(potentialExpandedUrl) > 0):

                        #create new entry for user since user is not in dictionary
                        potentialExpandedUrl = potentialExpandedUrl.strip()
                        if( tweet.user.screen_name in expandedUrlsDictionary):
                            expandedUrlsDictionary[tweet.user.screen_name].append(potentialExpandedUrl)
                        else:
                            expandedUrlsDictionary[tweet.user.screen_name] = [potentialExpandedUrl]

                        #add the created_at date for this tweet
                        globalDictionaryOfTweetExtraInformation[potentialExpandedUrl] = [tweet.id, localTimeTweet]
        else:
            break

    print("expandedUrlsDictionary: ", expandedUrlsDictionary)
    return expandedUrlsDictionary

def composeEmailString(expandedUrlsDictionary):

    if(len(expandedUrlsDictionary) > 0):
        emailString = 'Requests to whatdiditlooklike.tumblr.com\n\n'

        for user, url in expandedUrlsDictionary.items():
            emailString = emailString + user + ':\n'

            for u in url:
                emailString = emailString + '\t' + u + '\n'

        return emailString
    else:

        return emailString

def updateStatus(statusUpdateString, screen_name = '', tweet_id = ''):

    screen_name = screen_name.strip()
    tweet_id = tweet_id.strip()

    if(len(statusUpdateString) > 0):
        if(len(tweet_id) > 0 and len(screen_name) > 0):

            tweet_id = int(tweet_id)
            api.update_status('@'+ screen_name + ', ' + statusUpdateString, tweet_id)
        else:
            api.update_status(statusUpdateString)

def updateStatusWithMedia(statusUpdateString, filename, screen_name = '', tweet_id = ''):

    screen_name = screen_name.strip()
    tweet_id = tweet_id.strip()

    if(len(statusUpdateString) > 0 and len(filename) > 0):
        if(len(tweet_id) > 0 and len(screen_name) > 0):

            tweet_id = int(tweet_id)
            api.update_with_media(filename, '@'+ screen_name + ', ' + statusUpdateString, tweet_id)
        else:
            api.update_with_media(filename, statusUpdateString)

def sendSomeoneADirectMessage(screen_name, message):
    if(len(screen_name) > 0):
           api.send_direct_message(screen_name=screen_name, text=message) 

'''
    input: http://www.example.com
    In the event that the nominated URL has already been posted:
        1. check if the difference between the date it was posted exceeds the limit set,
        if so, this URL cannot go public
'''
def isThisURLWithinNominationDifferential_old(URL, tweetDateTime):

    dateDiff = 0
    returnValue = False

    URL = URL.strip()
    tweetDateTime = tweetDateTime.strip()

    if( len(URL) > 0 and len(tweetDateTime) > 0 ):


        # call to getFolderNameFromUrl get tld
        URL = getCanonicalUrl(URL)
        URLHash = getHash(URL)
        
        isPostedFlag = isPosted( URLHash )
        
        #if this url has been postedcheck if nominationDifferential has elapsed
        if( isPostedFlag == 1 ):

            try:

                maxDays = getConfigParameters('nominationDifferential')

                #get date of post

                inputFile = open(tumblrDataFileName, 'r')
                lines = inputFile.readlines()
                inputFile.close()



                for l in lines:

                    urlPostIDdateTimePosted = l.strip().split(', ')
                    urlPosted = urlPostIDdateTimePosted[0].strip()

                    #get tld
                    urlPosted = getCanonicalUrl(urlPosted)
                    urlPosted = urlPosted.strip()

                    #more normalization - start

                    URL = URL.lower()

                    if( URL[-1] != '/' ):
                        URL = URL + '/'

                    if( urlPosted[-1] != '/' ):
                        urlPosted = urlPosted + '/'
                    
                    #more normalization - end



                    if( URL == urlPosted ):

                        datePosted = urlPostIDdateTimePosted[2]

                        datePosted = datetime.strptime(datePosted, '%Y-%m-%d %H:%M:%S')
                        tweetDateTime = datetime.strptime(tweetDateTime, '%Y-%m-%d %H:%M:%S')

                        dateDiff = tweetDateTime - datePosted
                        dateDiff = int(str(dateDiff.days))


                        if( dateDiff > maxDays ):
                            returnValue = True

                        dateDiff = maxDays - dateDiff

                        break

            except:
                returnValue = False
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print((fname, exc_tb.tb_lineno, sys.exc_info() ))
        else:
            returnValue = True

    return returnValue, dateDiff

'''
    input: http://www.example.com
    In the event that the nominated URL has already been posted:
        1. check if the difference between the date it was posted exceeds the limit set,
        if so, this URL cannot go public
'''
def isThisURLWithinNominationDifferential(URL, tweetDateTime):

    dateDiff = 0
    returnValue = False

    URL = URL.strip()
    tweetDateTime = tweetDateTime.strip()

    if( len(URL) > 0 and len(tweetDateTime) > 0 ):

        URL = getCanonicalUrl(URL)
        URLHash = getFormattedTagURL(URL)
        
        isPostedFlag = isPosted( URLHash )

        #if this url has been postedcheck if nominationDifferential has elapsed
        if( isPostedFlag == 1 ):

            try:

                maxDays = getConfigParameters('nominationDifferential')

                #get post datetime from tumblr - start

                datePostedFromTumblr = getPostDateTime(URLHash)
                datePostedFromTumblr = datePostedFromTumblr.split(' ')

                datePostedFromTumblr = datePostedFromTumblr[0] + ' ' + datePostedFromTumblr[1]
                datePostedFromTumblr = datetime.strptime(datePostedFromTumblr, '%Y-%m-%d %H:%M:%S')
                localTimeTweet = datetime_from_utc_to_local(datePostedFromTumblr)

                tweetDateTime = datetime.strptime(tweetDateTime, '%Y-%m-%d %H:%M:%S')

                dateDiff = tweetDateTime - datePostedFromTumblr
                dateDiff = int(str(dateDiff.days))

                if( dateDiff > maxDays ):
                    returnValue = True
                
                dateDiff = abs(maxDays - dateDiff)

                #get post datetime from tumblr - end

            except:
                returnValue = False
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print((fname, exc_tb.tb_lineno, sys.exc_info() ))
        else:
            returnValue = True


    return returnValue, dateDiff

def extractRequestsFromTwitter():


    print("...getting potential requests from twitter")
    expandedUrlsDictionary = getRequestUrls()
    

    ###################################---------------TESTING-START---------------###################################
    #return
    ###################################---------------TESTING-END-----------------###################################
    
    #send tweet.user.screen_name that post has been made
    #cron job to retrieve this tweets


    if(len(expandedUrlsDictionary) > 0):

        #listOfAlreadyNotifiedTweetIDs = []
        goAheadFlag = False
        requestsFile = open(globalRequestFilename, "a")
        #send notifications
        for screen_name, urls in expandedUrlsDictionary.items():

            for u in urls:

                #globalDictionaryOfTweetExtraInformation[u][0] = tweet.id
                #globalDictionaryOfTweetExtraInformation[u][1] = created_at_datetime

                print()
                print(u)

                #check if this post has been made already - start
                print('...checking if post has been made already')
                goAheadFlag, dateDiff = isThisURLWithinNominationDifferential(u, str(globalDictionaryOfTweetExtraInformation[u][1]) )
                #check if this post has been made already - end

                #get page title - start

                pageTitle = getPageTitle(u)

                if( len(pageTitle) > 37 ):
                    pageTitle = pageTitle[0:36]
                    pageTitle = pageTitle + '...'

                #get page title - end

                notificationMessage = ''
                dateTime = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if( goAheadFlag ):
                    print('...post has not been made, composing notification message')
                    notificationMessage = '@'+ screen_name + ' Your request (' + u + ', '+ pageTitle +') was received at ' + dateTime
                else:

                    #TAG-MODIFICATION-ZONE
                    print('...post HAS been made, composing notification message')
                    notificationMessage = '@'+ screen_name + ' Your request ('+ dateTime +') has already been posted. Please retry in ' + str(dateDiff) + ' days: ' + globalBlogName + '/tagged/' + getFormattedTagURL(getCanonicalUrl(u))
                    #notify user post already exist and say when post can be renominated?

                try:
                    #send notification - start

                    #MOD
                    #print '...updating status ', notificationMessage
                    #print "...sending screen_name notification of receipt"
                    print('msg/u/id:', notificationMessage, u, globalDictionaryOfTweetExtraInformation[u][0])
                    api.update_status(notificationMessage, globalDictionaryOfTweetExtraInformation[u][0])
                    
                    #send notification - end

                    if( goAheadFlag ):
                        print("...writing requests to file")

                        requestsFile.write(u + ' <> ' + screen_name + ' <> ' + str(globalDictionaryOfTweetExtraInformation[u][1]) + ' <> ' + str(globalDictionaryOfTweetExtraInformation[u][0]) + '\n')
                        
                except:
                    print("")
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print((fname, exc_tb.tb_lineno, sys.exc_info() ))

                    #MOD
                    errorMessage = (fname, exc_tb.tb_lineno, sys.exc_info() )
                    sendErrorEmail( str(errorMessage) )

        '''
        if( goAheadFlag ):
            #send email to me - start
            emailString = composeEmailString(expandedUrlsDictionary)

            #send email to inform me about new requests
            if(len(emailString) > 0):
                
                
                #sender = 'anwala@cs.odu.edu'
                #receivers = ['anwala@cs.odu.edu','alexandersconception@yahoo.com']
                #message = 'this is a test message'
                #subject = 'test email service'
                #sendEmail(sender, receivers, subject, message)#

                sender = 'anwala@cs.odu.edu'
                receivers = ['anwala@cs.odu.edu','alexandersconception@yahoo.com']
                message = 'twitter_requests_wdill.txt'

                subject = 'New requests to whatdiditlooklike'
                #MOD
                print "...sending email of requests"
                sendEmail(sender, receivers, subject, message)

            #send email to me - end
        '''

        requestsFile.close()


#test with tweets that across multiple pages
#getRequestUrls()


def main():

    #debug - start
    

    extractRequestsFromTwitter()

    #MOD
    print('...calling usingTimelapseToTakeScreenShots.py')

    pythonVirtualEnvPath = getConfigParameters('pythonVirtualEnv1Path')
    os.system(pythonVirtualEnvPath + ' -u ' + globalPrefix + 'usingTimelapseToTakeScreenShots.py &')


    #debug - end



if __name__ == "__main__":
   main()