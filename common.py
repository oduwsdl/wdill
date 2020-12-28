import pytumblr
import os, sys, traceback
import glob
import re
import time
from datetime import datetime

import requests
import subprocess
import hashlib
from random import randint

from timelapse import getCanonicalUrl
from timelapse import getFolderNameFromUrlOld2
from getConfig import getConfigParameters

globalBlogName = getConfigParameters('globalBlogName')
globalPrefix = getConfigParameters('globalPrefix')
messageSuiteFileName = globalPrefix + 'statusUpdateMessageSuite.txt'

# Authenticate via OAuth
tumblrConsumerKey = getConfigParameters('tumblrConsumerKey')
tumblrConsumerSecret = getConfigParameters('tumblrConsumerSecret')
tumblrAccessToken = getConfigParameters('tumblrAccessToken')
tumblrAccessTokenSecret = getConfigParameters('tumblrAccessTokenSecret')

client = pytumblr.TumblrRestClient(
  tumblrConsumerKey,
  tumblrConsumerSecret,
  tumblrAccessToken,
  tumblrAccessTokenSecret
)


'''
	input:canonicalURL
'''
def getFormattedTagURL(canonicalURL):

	
	canonicalURL = canonicalURL.strip()
	if( len(canonicalURL) > 0 ):
		canonicalURL = re.sub(r'\W+', '.', canonicalURL)

	return canonicalURL

'''
	input:canonicalURL
'''
def getHashString(canonicalURL):

	md5hash = ''
	canonicalURL = canonicalURL.strip()
	if( len(canonicalURL) > 0 ):

		
		# Assumes the default UTF-8; http://www.pythoncentral.io/hashing-strings-with-python/
		hash_object = hashlib.md5(canonicalURL.encode())
		md5hash = hash_object.hexdigest()

	return md5hash

#precondition: first line: What Did http://www.example.com Look Like From beginYear To EndYear?
def extractBeginAndEndYear(firstLineOfUrlsFile):
	if( len(firstLineOfUrlsFile) > 0 ):
		indexOfFrom = firstLineOfUrlsFile.rfind('From')
		#index of "From" + length of "From"
		years = firstLineOfUrlsFile[indexOfFrom + 4:]
		#remove ?
		years = years[:-1]
		years = years.split('To')
		
		beginYear = years[0].strip()
		endYear = years[1].strip()

		return beginYear, endYear

#precondition gif filname has OptDelay
def getGifFilename(folderName):

	newfile = ''
	if(len(folderName) > 0):

		currentFolder = os.getcwd()
		os.chdir(folderName)
		for file in glob.glob("*.gif"):

			indexOfMarker = file.find("Delay")
			if(indexOfMarker > -1):

				newfile = file[:indexOfMarker] + 'Opt' + file[indexOfMarker:]
				break

		os.chdir(currentFolder)

	return newfile

#precondition: links file is called urlsFile.txt
def getLinks(folderName):

	folderName = folderName.strip()
	if( len(folderName) > 0 ):
		
		try:
			urlsFile = open(globalPrefix + '/' + folderName + '/urlsFile.txt', 'r')
			urls = urlsFile.read()
			urlsFile.close()

			return urls
		except:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print((fname, exc_tb.tb_lineno, sys.exc_info() ))

#returns post id, beginYear, endYear
def uploadAnimatedGifToSocialMedia(folderName, URL, queueOrPublish='queue'):

	
	folderName = folderName.strip()
	URL = URL.strip()
	if( len(folderName) > 0 and len(URL) > 0 and (queueOrPublish == 'queue' or queueOrPublish =='publish') ):

		tldURL = getFolderNameFromUrlOld2(URL)

		canonicalURL = getCanonicalUrl(URL)
		#TAG-MODIFICATION-ZONE
		canonicalURL = getFormattedTagURL(canonicalURL)
		
		if( canonicalURL != tldURL ):
			tags = canonicalURL + ',' + tldURL
		else:
			tags = canonicalURL

		links = getLinks(folderName)

		indexOfNewLineCharacter = links.find('\n')
		firstline = links[:indexOfNewLineCharacter]

		beginYear, endYear = extractBeginAndEndYear(firstline)
		gifAnimationFilename = getGifFilename(folderName)
		mp4Filename = globalPrefix + folderName + '/' + folderName + 'WithAudio.mp4'

		if(len(mp4Filename) > 0):
			#instagram currently doesn't support posting videos via a web browser
			'''
			instaScript = os.path.join(os.path.dirname(__file__), globalPrefix+'instagram.js')
			username = getConfigParameters('instagramUsername')
			password = getConfigParameters('instagramPassword')
			nodeSystemPath = getConfigParameters('nodeSystemPath')
			print("...uploading to instagram")
			res = subprocess.check_output([nodeSystemPath, instaScript, username, password, globalPrefix + folderName + '/' + folderName + '.mp4', links])
			instagramLink = res.decode('utf-8')
			print(instagramLink)
			instagramLink = instagramLink.replace('\n',"")
			instagramLink = instagramLink.replace('Instagram Link: ','')
			'''

			instaScript = os.path.join(os.path.dirname(__file__), globalPrefix+'instagramWithBrowserStack.py')
			username = getConfigParameters('instagramUsername')
			password = getConfigParameters('instagramPassword')
			browserStackUserID = getConfigParameters('browserStackUserID')
			browserStackKey = getConfigParameters('browserStackKey')
			instaAppPath = glob.glob(globalPrefix+"*.apk")[0]

			print("...uploading to Instagram")
			pythonVirtualEnvPath = getConfigParameters('pythonVirtualEnv1Path')
			instaCaption = links[0].replace("\n","") + " #memento"
			res = subprocess.check_output([pythonVirtualEnvPath, instaScript, username, password, browserStackUserID, browserStackKey, instaAppPath, mp4Filename, instaCaption])
			instagramLink = res.decode('utf-8')
			instagramLink = instagramLink.replace('\n',"")
			instagramLink = instagramLink.split('Instagram Link: ')[-1]
			instagramLink = re.sub('^https?:\/\/(www\.)?', '', instagramLink.split('/?')[0])
			print(instagramLink)
			
			print("...uploading to tumblr")
			postID = client.create_video(globalBlogName, tags=[tags], state=queueOrPublish, caption=[links], data=mp4Filename)
			#postID = client.create_photo(globalBlogName, tags=[tags], state=queueOrPublish, caption=[links], data=globalPrefix + folderName + '/' + gifAnimationFilename)
			#write this postID to tumblrDataFile.txt
			return postID['id'], beginYear, endYear, instagramLink

	return -1, '', '', ''

def getPostDateTime(postTag):

	postTag = postTag.strip()
	postDateTime = ''

	if( len(postTag) ):

		params = {'tag': postTag, 'limit': 1}
		postJson = client.posts(globalBlogName, **params)

		postDateTime = postJson['posts'][0]['date']



	return postDateTime

def getPostID(postTag):

	postTag = postTag.strip()
	postID = ''

	if( len(postTag) ):

		params = {'tag': postTag, 'limit': 1}
		postJson = client.posts(globalBlogName, **params)
		postID = postJson['posts'][0]['id']

	return postID

#http://stackoverflow.com/questions/4770297/python-convert-utc-datetime-string-to-local-datetime
def datetime_from_utc_to_local(utc_datetime):
	now_timestamp = time.time()
	offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
	return utc_datetime + offset


'''
	input: canonicalURLHash
	return value:
	   -1 - error
		0 - not posted
		1 - posted
'''
def isPosted(canonicalURLHash):

	
	returnCode = 0
	canonicalURLHash = canonicalURLHash.strip()
	if( len(canonicalURLHash) > 0 ):

		
		canonicalURLHash = 'https://'+globalBlogName+'/tagged/'+canonicalURLHash
		

		try:
			'''
			co = 'curl -I -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36" "'+canonicalURLHash+'"'
			header = subprocess.getoutput(co)

			if(header.find('HTTP/1.1 200 OK') > -1):
				returnCode = 1
			'''
			req = requests.get(canonicalURLHash)
			if req.status_code == 200:
				returnCode = 1
		except:
			returnCode = -1
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print((fname, exc_tb.tb_lineno, sys.exc_info() ))

	return returnCode

def getRandomStatusUpdateMessage(folderNameUrl, pageTitle, beginYear, endYear, link):

	randomMessage = ''

	if( len(folderNameUrl) > 0 and len(pageTitle) > 0 and len(link) > 0 and len(beginYear) > 0 and len(endYear) > 0 ):

		try:
			messageSuiteFile = open(messageSuiteFileName, 'r')
			lines = messageSuiteFile.readlines()

			messageCount = len(lines)
			if( messageCount > 0 ):

				randomMessageIndex = randint(0, messageCount-1)
				randomMessage = lines[randomMessageIndex].strip()

				folderNameUrl = folderNameUrl.strip()
				pageTitle = pageTitle.strip()
				beginYear = beginYear.strip()
				endYear = endYear.strip()
				link = link.strip()

				randomMessage = randomMessage.replace('folderName', folderNameUrl)
				randomMessage = randomMessage.replace('pageTitle', pageTitle)
				randomMessage = randomMessage.replace('beginYear', beginYear)
				randomMessage = randomMessage.replace('endYear', endYear)
				randomMessage = randomMessage.replace('link', link)
				#randomMessage = randomMessage + '\n#memento'

		except:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print((fname, exc_tb.tb_lineno, sys.exc_info() ))
			
	
	return randomMessage

def getPageTitle(url):

	titleOfPage = ''
	if( len(url) > 0 ):

		try:
			req = urllib.request.Request(url)
			req.add_header('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.101 Safari/537.36')

			response = urllib.request.urlopen(req)
			soup = BeautifulSoup(response)

			titleOfPage = soup.title.string

			#this line added because some titles contain funny characters that generate encoding errors
			titleOfPage = titleOfPage.encode('ascii', 'ignore')
		except:
			titleOfPage = url + '...'

	return titleOfPage