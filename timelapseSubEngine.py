import os, sys
import subprocess
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error

import datetime
from datetime import datetime
import time

from bs4 import BeautifulSoup

from sendEmail import sendErrorEmail
from getConfig import getConfigParameters

from timelapseRunGateway import checkRunCount
from timelapse import getCanonicalUrl

from timelapseTwitter import updateStatus
from timelapseTwitter import updateStatusWithMedia
from timelapseTwitter import isThisURLWithinNominationDifferential

from common import getHashString
from common import getFormattedTagURL
from common import extractBeginAndEndYear
from common import getLinks
from common import uploadAnimatedGifToSocialMedia
from common import isPosted
from common import getPageTitle
from common import getRandomStatusUpdateMessage
from common import getPostID
from common import getPostDateTime


globalBlogName = getConfigParameters('globalBlogName')
globalPrefix = getConfigParameters('globalPrefix')

runCountFileName = globalPrefix + 'runCountTSE.txt'
globalDataFileName = globalPrefix + 'twitter_requests_wdill.txt'
globalDataStoreFileName = globalPrefix + 'twitter_requests_wdill_store.txt'
debugOutputFileName = globalPrefix + 'debugOutputFile.txt'



def makeStatusUpdateAndNotifyReferrer(twitterStatusUpdateMessage, screen_nameOfUserWhoSuggestedUri, tweet_id, URL, link, filename):

	modifyEntryFlag = False
	twitterStatusUpdateMessage = twitterStatusUpdateMessage.strip()
	if( len(twitterStatusUpdateMessage) > 0 ):
		try:
			
			print('...status update:', twitterStatusUpdateMessage.strip() + '\n#memento')
			#MOD
			updateStatus(twitterStatusUpdateMessage.strip() + '\n#memento')
			
			modifyEntryFlag = True
		except:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print((fname, exc_tb.tb_lineno, sys.exc_info() ))

			debugOutputFile = open(debugOutputFileName, 'w')
			debugOutputFile.write('status update message: ' + twitterStatusUpdateMessage + '\n')
			debugOutputFile.write(fname + ', ' + str(exc_tb.tb_lineno) + ', ' + str(sys.exc_info()) + '\n')

			errorMessage = (fname, exc_tb.tb_lineno, sys.exc_info() )
			sendErrorEmail( str(errorMessage) )
	

		print("...sending " + screen_nameOfUserWhoSuggestedUri + " direct message")

	screen_nameOfUserWhoSuggestedUri = screen_nameOfUserWhoSuggestedUri.strip()
	tweet_id = tweet_id.strip()
	URL = URL.strip()
	link = link.strip()
	if( len(screen_nameOfUserWhoSuggestedUri) > 0 and len(tweet_id) > 0 and len(URL) > 0 and len(link) > 0 ):
		try:
			
			#sendSomeoneADirectMessage(screen_nameOfUserWhoSuggestedUri, 'Hello ' + screen_nameOfUserWhoSuggestedUri + ',\n' + getCanonicalUrl(URL) + ' has been posted on http://bit.ly/whatdiditlooklike')
			#send a message under the same thread

			pageTitle = getPageTitle('http://' + getCanonicalUrl(URL) )

			if( len(pageTitle) > 40 ):
				pageTitle = pageTitle[0:39]
				pageTitle = pageTitle + '...'

			notificationMessage = ' ' + getCanonicalUrl(URL) + ' (' + pageTitle + ') has been posted: ' + link
			
			print('...status notification', notificationMessage)
			#MOD
			updateStatusWithMedia(statusUpdateString=notificationMessage, screen_name=screen_nameOfUserWhoSuggestedUri, tweet_id=tweet_id, filename=filename)
			modifyEntryFlag = True
		except:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print((fname, exc_tb.tb_lineno, sys.exc_info() ))

			debugOutputFile = open(debugOutputFileName, 'w')
			debugOutputFile.write('status update message: ' + twitterStatusUpdateMessage + '\n')
			debugOutputFile.write(fname + ', ' + str(exc_tb.tb_lineno) + ', ' + str(sys.exc_info()) + '\n')

			errorMessage = (fname, exc_tb.tb_lineno, sys.exc_info() )
			sendErrorEmail( str(errorMessage) )

	return modifyEntryFlag

def postToTumblrQueue():

	print('...post to queue called')

	#get new items to post:
	nominationTuples = []
	try:
		nominationsFile = open(globalDataFileName, "r")
		nominationTuples = nominationsFile.readlines()
		nominationsFile.close()
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print((fname, exc_tb.tb_lineno, sys.exc_info() ))
		nominationsFile.close()
		return


	print("read lines: ", len(nominationTuples))

	if( len(nominationTuples) > 0):


		#<index, [int(POST-ID), str(STATUS-UPDATE-WHEN-PUBLIC)]>
		dictionaryOfLinesToModify = {}

		for i in range(0,len(nominationTuples)):
			nominationData = nominationTuples[i].split(' <> ')
			print('...nominationData:',nominationData)
			'''
			0: URL
			1: SCREEN-NAME
			2: DATE-TIME
			3: TWEET-ID
			(optional 
				4: POST-ID
				5: STATUS-UPDATE-WHEN-PUBLIC
				6: POST-FLAG
			'''
			#this url has not been posted, so post to queue
			if( len(nominationData) < 5):

				URL = nominationData[0].strip()
				screen_name = nominationData[1].strip()
				tweetDateTimeString = nominationData[2].strip()
				tweetID = nominationData[3].strip()

				canonicalURL = getCanonicalUrl(URL)
				folderName = ''
				
				#check if this post has been made already - start
				
				print('...checking if post has been made already')
				
				#CAUTION - start
				#check not required since timelapseTwitter.py runs before timelapseSubEngine.py
				#and does the isThisURLWithinNominationDifferential() check
				#goAheadFlag, dateDiff = isThisURLWithinNominationDifferential(URL, tweetDateTimeString)
				goAheadFlag = True
				#CAUTION - end




				#check if this post has been made already - end

				formattedTag = getFormattedTagURL(canonicalURL)
				#this URL is not public
				if( goAheadFlag ):
					#debug - start
					#uploadAnimatedGifToTumblr(URL)

					#folderName is hash
					folderName = getHashString(canonicalURL)
					print('...hashFolderName:', folderName)
					postID, beginYear, endYear  = uploadAnimatedGifToSocialMedia(folderName, URL)

					#print 'folderName', folderName
					#postID = 123
					#beginYear = '1997'
					#endYear = '2014'
					#debug - end

					#if post is successful, get a status update message - start
					#TAG-MODIFICATION-ZONE
					link = globalBlogName + '/tagged/' + formattedTag
					pageTitle = getPageTitle('http://' + canonicalURL )
					pageTitle = pageTitle.strip()

					#folderNameUrl - 22
					#link - 22
					#beginYear - 4
					#endYear - 4
					#pageTitle - variable
					#\n#memento - 9
					#max pageTitle is 42 
					#memento 8
					if( len(pageTitle) > 40 ):
						pageTitle = pageTitle[0:39]
						pageTitle = pageTitle + '...'
					twitterStatusUpdateMessage = getRandomStatusUpdateMessage(canonicalURL, pageTitle, beginYear, endYear, link)
					print('...status update message when public: ', twitterStatusUpdateMessage)

				else:
					#this URL is already public probably due to TME, so notify referrer and trick notify notifyOnPostApproved() by adding public so it will skip this entry
					twitterStatusUpdateMessage = 'STATUS UPDATE MESSAGE <> PUBLIC'
					beginYear = '0000'
					endYear = '0000'
					postID = '0000'

					#TAG-MODIFICATION-ZONE
					notificationMessage = ' Your request ('+ tweetDateTimeString +') has already been posted. Please retry in ' + str(dateDiff) + ' days: ' + globalBlogName + '/tagged/' + formattedTag
					#MOD
					updateStatus(statusUpdateString=notificationMessage, screen_name=screen_name, tweet_id=tweetID)
				




				#if post is successful, get a status update message - end
				if( len(twitterStatusUpdateMessage)>0 and len(folderName)>0 and len(beginYear)>0 and len(endYear)>0 and postID>0 ):
					dictionaryOfLinesToModify[i] = [ postID, twitterStatusUpdateMessage ]

		#if a new post has been placed on the queue modify entry line in input file
		if( len(dictionaryOfLinesToModify) > 0 ):

			#modify input lines with new data due to post on queue

			for index, postDataArray in list(dictionaryOfLinesToModify.items()):
				postID = str(postDataArray[0])
				twitterStatusUpdateMessageWhenPublic = postDataArray[1]
				nominationTuples[index] = nominationTuples[index].strip() + ' <> ' + postID + ' <> ' + twitterStatusUpdateMessageWhenPublic + '\n'

			try:
				nominationsFile = open(globalDataFileName, 'w')
				nominationsFile.writelines(nominationTuples)
				nominationsFile.close()

				#send notification email - start
				sendErrorEmail('wdill - new items in queue', 'Queue Event Notification')
				#send notification email - end
			except:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print((fname, exc_tb.tb_lineno, sys.exc_info() ))
				nominationsFile.close()
				return

def notifyOnPostApproved():

	print('...notify called')

	nominationTuples = []
	try:
		nominationsFile = open(globalDataFileName, "r")
		nominationTuples = nominationsFile.readlines()
		nominationsFile.close()
	except:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print((fname, exc_tb.tb_lineno, sys.exc_info() ))
		nominationsFile.close()
		return

	print("read lines: ", len(nominationTuples))
	if( len(nominationTuples) > 0):

		
		indicesOfLinesToModify = []

		for i in range(0,len(nominationTuples)):
			nominationData = nominationTuples[i].split(' <> ')


			'''
			nominationData:
			0: URL
			1: SCREEN-NAME
			2: DATE-TIME
			3: TWEET-ID
			(status 
				4: POST-ID
				5: STATUS-UPDATE-WHEN-PUBLIC
				6: POST-FLAG
			)
			'''
			#this url has been posted on queue, so check if approved published
			if( len(nominationData) == 6 ):

				URL = nominationData[0].strip()
				tweetDateTime = nominationData[2].strip()
				postID = nominationData[4].strip()
				canonicalURL = getCanonicalUrl(URL)

				formattedTag = getFormattedTagURL(canonicalURL)
				folderName = ''

				#TAG-MODIFICATION-ZONE
				link = 'http://'+globalBlogName+'/tagged/'+ formattedTag
				print('...checking for public status URL/canonicalURL:', URL, canonicalURL)

				
				isPostedFlag = isPosted(formattedTag)
				#this url has been published so mark for line append with 'public'

				if isPostedFlag == 1:

					postDateTimeIsGreaterThanTweetDateTimeFlag = False
					#does the tweet datetime predate the post datetime - start : this is a measure to ensure we are looking at the
					#right post in the case of multiple posts

					#check if post datetime is greater than tweet datetime
					#tweetDateTime

					#TAG-MODIFICATION-ZONE
					datePostedFromTumblr = getPostDateTime(formattedTag)
					datePostedFromTumblr = datePostedFromTumblr.split(' ')
					datePostedFromTumblr = datePostedFromTumblr[0] + ' ' + datePostedFromTumblr[1]
					
					datePostedFromTumblr = datetime.strptime(datePostedFromTumblr, '%Y-%m-%d %H:%M:%S')
					tweetDateTime = datetime.strptime(tweetDateTime, '%Y-%m-%d %H:%M:%S')

					if( datePostedFromTumblr >= tweetDateTime ):
						postDateTimeIsGreaterThanTweetDateTimeFlag = True
					else:
						print('...course correction, this post hasn\'t gone public, but a public sibling')

					#does the tweet datetime predate the post datetime - end

					if( postDateTimeIsGreaterThanTweetDateTimeFlag ):

						#get new post ID - start

						postID = str( getPostID(getFormattedTagURL(canonicalURL)) )
						print('...getting new postID', postID)
						#get new post ID - end
						

						#if this post has gone public, status update, notify referrer

						screenNameOfUserWhoSuggestedURI = nominationData[1].strip()
						tweetID = nominationData[3].strip()
						statusUpdateMessage = nominationData[5].strip()
						
						folderName = getHashString(canonicalURL)
						filename = './'+folderName+'/'+folderName+'OptDelay4.gif'

						modifyEntryFlag = makeStatusUpdateAndNotifyReferrer(statusUpdateMessage, screenNameOfUserWhoSuggestedURI, tweetID, URL, link, filename)

						#if notification to referrer went well, modify entry in file
						
						if( modifyEntryFlag ):
							indicesOfLinesToModify.append(i)#caution, mutually exclusive with twin statement above

							#rename folder so as to permit renomination - start
							now = datetime.now()

							nowFolderAppend = str(now.strftime("%Y-%m-%d_%H-%M-%S"))
							now = str(now.strftime("%Y-%m-%d %H:%M:%S"))

							#get folderName - start
								
							folderName = getHashString(canonicalURL)
							print('...hashFolderName:', folderName)

							#get folderName - end

							nowFolderAppend = '_' + nowFolderAppend
							
							print('...renaming', folderName + nowFolderAppend)
							#MOD
							os.rename(folderName, folderName + nowFolderAppend)
							print()

							#rename folder so as to permit renomination - end

							#update tumblrUrlsDataFile.txt with <URL, PostID, now> - start
							#tumblrURLsInputFile = open(tumblrDataFileName, 'a')
							#tumblrURLsInputFile.write(URL + ', ' + postID + ', ' + now + '\n')
							#tumblrURLsInputFile.close()
							#update tumblrUrlsDataFile.txt with <URL, PostID, now> - end



		if( len(indicesOfLinesToModify) > 0 ):
			try:
				inputStoreFile = open(globalDataStoreFileName, 'a')

				for index in indicesOfLinesToModify:
					#write to store file, then delete
					print('...moving entry to store', nominationTuples[index])
					inputStoreFile.write(nominationTuples[index].strip() + ' <> ' + 'PUBLIC' + '\n')
					
					#mark for removal
					nominationTuples[index] = ' '

				inputStoreFile.close()

				nominationsFile = open(globalDataFileName, 'w')
				#adjust list: remove those who have gone public (moved to store) - start
				for entry in nominationTuples:
					if( entry != ' ' ):
						nominationsFile.write(entry.strip() + '\n')
				#adjust list: remove those who have gone public (moved to store) - end
				nominationsFile.close()
			except:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print((fname, exc_tb.tb_lineno, sys.exc_info() ))

def main():

	maxTimesToRunTSE = getConfigParameters('maxTimesToRunTSE')
	shouldIRunFlag = checkRunCount(maxTimesToRunTSE, '.', runCountFileName)
	if( shouldIRunFlag ):
		#post to queue, create status update message to modify line in file
		postToTumblrQueue()
		#notifyOnPostApproved()
		print('...DONE')
	else:
		print('...runCount exceeded')
	
	
	
if __name__ == "__main__":
	main()

#customMainFunction()
#isPosted('http://whatdiditlooklike.tumblr.com/tagged/www.facebook.com')

'''
#testURL = 'http://www.cs.odu.edu/'
#folderName = getFolderNameFromUrl(testURL)


#post to queue
postID, beginYear, endYear  = uploadAnimatedGifToTumblr(folderName)

#has referred post gone public?
if it has gone public make a status update and notify the referrer
print isPosted('http://whatdiditlooklike.tumblr.com/tagged/'+folderName)
'''