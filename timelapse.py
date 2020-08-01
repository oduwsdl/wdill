import subprocess
import time
import datetime
import sys
import argparse, os
import subprocess
import hashlib
import tldextract
import urllib.parse
import glob
import json
import requests

from subprocess import call
from os import walk

from surt import handyurl
from surt.IAURLCanonicalizer import canonicalize

from getConfig import getConfigParameters
from sendEmail import sendErrorEmail



globalPrefix = getConfigParameters('globalPrefix')
globalMementoUrlDateTimeDelimeter = "*+*+*"
#deprecated
#globalDataFileName = '/home/anwala/wsdl/projects/timelapse/webshots/tumblrUrlsDataFile.txt'

'''
	assumption: entries are delimited by newline
	format LANL:
	<http://www.webcitation.org/64ta04WpM>; rel="first memento"; datetime="Mon, 23 Jan 2012 02:01:29 GMT",
	<http://www.webcitation.org/6ChPDhqw8>; rel="memento"; datetime="Thu, 06 Dec 2012 03:45:27 GMT",
	<http://www.webcitation.org/6ChPHTKJY>; rel="last memento"; datetime="Thu, 06 Dec 2012 03:46:23 GMT"

	format CS:
	, <http://www.webcitation.org/64ta04WpM>; rel="first memento"; datetime="Mon, 23 Jan 2012 02:01:29 GMT",
	, <http://www.webcitation.org/6ChPDhqw8>; rel="memento"; datetime="Thu, 06 Dec 2012 03:45:27 GMT",
	, <http://www.webcitation.org/6ChPHTKJY>; rel="last memento"; datetime="Thu, 06 Dec 2012 03:46:23 GMT"

'''
def getItemGivenSignature(page):

	listOfItems = []
	if( len(page) > 0 ):
		page = page.splitlines()
		for line in page:
			if(line.find('memento";') != -1):
				#uriRelDateTime: ['<http://www.webcitation.org/64ta04WpM>', ' rel="first memento"', ' datetime="Mon, 23 Jan 2012 02:01:29 GMT",']
				uriRelDateTime = line.split(';')
				if( len(uriRelDateTime) > 2 ):
					if( uriRelDateTime[0].find('://') != -1 ):
						if( uriRelDateTime[2].find('datetime="') != -1 ):


							uri = ''
							uri = uriRelDateTime[0].split('<')
							#print uri
							if( len(uri) > 1 ):
								uri = uri[1].replace('>', '')
								uri = uri.strip()

							datetime = ''
							datetime = uriRelDateTime[2].split('"')
							if( len(datetime) > 1 ):
								datetime = datetime[1]
							
							if( len(uri) != 0 and len(datetime) != 0 ):
								#print uri, '---', datetime
								listOfItems.append(uri + globalMementoUrlDateTimeDelimeter + datetime)

	return listOfItems

def getItemGivenSignatureOld2(page):

	if( len(page) > 0 ):
		splitPages0 = page.split(', <')

		listOfItems = []


		for i in range(1, len(splitPages0)):

			#splitPagesAgain[url,rel,datetime]
			if( splitPages0[i].find(';') > -1 ):
				splitPagesAgain = splitPages0[i].split(';')

				#memento signature
				if( splitPagesAgain[1] == 'rel="memento"' ):

					url = splitPagesAgain[0]
					url = url[0:len(url)-1]

					
					if(len(splitPagesAgain)>2):
						if( splitPagesAgain[2].find(' datetime="')> -1 ):
							date = splitPagesAgain[2].strip(' datetime="')
							date = date[0:len(date)-2]

					#print url , globalMementoUrlDateTimeDelimeter, date
					listOfItems.append(url + globalMementoUrlDateTimeDelimeter + date)
		
		return listOfItems	

def getItemGivenSignatureOld(signatureString, endMarkerString, page):

	if( len(signatureString) > 0 and len(endMarkerString)> 0 and len(page) > 0):
		locationOfSignature = 0
		locationOfSecondSignature = 0
		#this logic is meant to retrieve date from a string of form: "<endMarkerString> Item <signatureString>"
		
		dateTimeMarker = 'datetime="'
		listOfItems = []

		while(locationOfSignature != -1):
		
			locationOfSignature = page.find(signatureString, locationOfSignature)
			locationOfSecondSignature = page.find(dateTimeMarker, locationOfSecondSignature)

			if(locationOfSignature != -1 and locationOfSecondSignature != -1):

				k = locationOfSignature
				k = k - 1
				
				url = ''
				#date = ''
				#date = page[k + len(signatureString) + 12:k + len(signatureString)+41]

				
				date2 = ''
				#get datetime="datetime"
				i = locationOfSecondSignature + len(dateTimeMarker)
				while(page[i] != '"'):
					date2 = date2 + page[i]
					i = i + 1
				date2 = date2.strip()

				locationOfSecondSignature = locationOfSecondSignature + len(dateTimeMarker)
				
				#get url
				while k > -1:
					#end marker
					if page[k] != endMarkerString :
						url = page[k] + url
					else :
						break
					k = k - 1;
				locationOfSignature = locationOfSignature + len(signatureString)

				url = url.strip()
				#date = date.strip()
				
				print("date2: ", date2)
				listOfItems.append(url + globalMementoUrlDateTimeDelimeter + date2)
			else :
					break
		
		#retrieve date from preceding " - </span>" signature - end
		return listOfItems

def getMementosPages(url):

	pages = []
	url = url.strip()
	if(len(url)>0):

		firstChoiceAggregator = getConfigParameters('mementoAggregator')
		timemapPrefix = firstChoiceAggregator + url
		#timemapPrefix = 'http://mementoproxy.cs.odu.edu/aggr/timemap/link/1/' + url

		'''
			The CS memento aggregator payload format:
				[memento, ..., memento, timemap1]; timemap1 points to next page
			The LANL memento aggregator payload format:
				1. [timemap1, ..., timemapN]; timemapX points to mementos list
				2. [memento1, ..., mementoN]; for small payloads

			For LANL Aggregator: The reason the link format is used after retrieving the payload
								 with json format is due to the fact that the underlying code is based
								 on the link format structure. json format was not always the norm 
		'''



		#select an aggregator - start
		aggregatorSelector = ''

		co = 'curl --silent -I ' + timemapPrefix
		head = subprocess.getoutput(co)

		indexOfFirstNewLine = head.find('\n')
		if( indexOfFirstNewLine > -1 ):

			if( head[:indexOfFirstNewLine].split(' ')[1] != '200' ):
				firstChoiceAggregator = getConfigParameters('mementoAggregator')
				timemapPrefix = firstChoiceAggregator + url

		if( firstChoiceAggregator.find('cs.odu.edu') > -1 ):
			aggregatorSelector = 'CS'
		else:
			aggregatorSelector = 'LANL'

		print('...using aggregator:', aggregatorSelector)
		#select an aggregator - end

		#CS aggregator
		if( aggregatorSelector == 'CS' ):
			while( True ):
				#old: co = 'curl --silent ' + timemapPrefix
				#old: page = commands.getoutput(co)

				
				page = ''
				r = requests.get(timemapPrefix)
				print('status code:', r.status_code)
				if( r.status_code == 200 ):
					page = r.text

				pages.append(page)
				indexOfRelTimemapMarker = page.rfind('>;rel="timemap"')

				if( indexOfRelTimemapMarker == -1 ):
					break
				else:
					#retrieve next timemap for next page of mementos e.g retrieve url from <http://mementoproxy.cs.odu.edu/aggr/timemap/link/10001/http://www.cnn.com>;rel="timemap"
					i = indexOfRelTimemapMarker -1
					timemapPrefix = ''
					while( i > -1 ):
						if(page[i] != '<'):
							timemapPrefix = page[i] + timemapPrefix
						else:
							break
						i = i - 1
		else:
			#LANL Aggregator
			#old: co = 'curl --silent ' + timemapPrefix
			#old: page = commands.getoutput(co)

			page = ''
			r = requests.get(timemapPrefix)
			if( r.status_code == 200 ):
				page = r.text

			try:
				payload = json.loads(page)

				if 'timemap_index' in payload:

					for timemap in payload['timemap_index']:
						
						timemapLink = timemap['uri'].replace('/timemap/json/', '/timemap/link/')
						#old: co = 'curl --silent ' + timemapLink
						#old: page = commands.getoutput(co)
						#old: pages.append(page)
						r = requests.get(timemapLink)
						if( r.status_code == 200 ):
							pages.append(r.text)
					
				elif 'mementos' in payload:
					#untested block
					timemapLink = payload['timemap_uri']['json_format'].replace('/timemap/json/', '/timemap/link/')
					#old: co = 'curl --silent ' + timemapLink
					#old: page = commands.getoutput(co)
					#old: pages.append(page)

					print('timemap:', timemapLink)
					r = requests.get(timemapLink)
					if( r.status_code == 200 ):
						pages.append(r.text)
					
				
				
			except:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print((fname, exc_tb.tb_lineno, sys.exc_info() ))

			
			
	return pages


'''
	input:canonicalURL
'''
def getHash(canonicalURL):

	md5hash = ''
	canonicalURL = canonicalURL.strip()
	if( len(canonicalURL) > 0 ):

		
		# Assumes the default UTF-8; http://www.pythoncentral.io/hashing-strings-with-python/
		hash_object = hashlib.md5(canonicalURL.encode())
		md5hash = hash_object.hexdigest()

	return md5hash

#returns a dictionary of <year, url> tuples. Given multiple instances of same year, only first is considered
def get1MementoPerYear(mementos, delimeterCharacter):

	if( len(mementos)>0 ):
		errorCount = 1
		yearUrlDictionary = {}

		for i in range(0, len(mementos)):
			for meme in mementos[i]:

				urlAndDateTime = meme.split(delimeterCharacter)
				#print urlAndDateTime
				try:
					date = time.strptime(urlAndDateTime[1], '%a, %d %b %Y %H:%M:%S %Z')
					if date.tm_year not in yearUrlDictionary:
						yearUrlDictionary[date.tm_year] = urlAndDateTime[0]
				except:
					date = errorCount
					print("date exception, ", urlAndDateTime[1])
					#print " 0:", urlAndDateTime[0]
					#print " 1:", urlAndDateTime[1]
					#print " 2:", urlAndDateTime[2]
					
					if date not in yearUrlDictionary:
						yearUrlDictionary[date] = urlAndDateTime[0]
					errorCount = errorCount + 1
			
			
		return yearUrlDictionary


	else:
		print("mementos list length = 0")

def getCanonicalUrl(URL):

    netloc = ''
    path = ''
    params = ''
    query = ''
    fragment = ''

    URL = URL.strip()
    if( len(URL)>0 ):
    	
        canonicalURL = handyurl.parse(URL)
        canonicalURL = canonicalize(canonicalURL).getURLString()

        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(canonicalURL)

    returnValue = netloc + path + params + query + fragment

    #normalize url
    if( returnValue[-1] == '/' ):
    	returnValue = returnValue[:-1]

    return returnValue

def extractYearFromUrl(url):
	if(len(url) > 0):
		
		#http://www.webarchive.org.uk:80/wayback/archive/20090101092312/http://www.google.com/
		#signature: ://
		lasIndexOfSignatureMarker = url.rfind("://")

		if( lasIndexOfSignatureMarker > -1 ):
			url = url[:lasIndexOfSignatureMarker]
			lasIndexOfSignatureMarker = url.rfind("/")

		lasIndexOfSignatureMarker = lasIndexOfSignatureMarker - 1
		yearExtract = ''

		for i in range(lasIndexOfSignatureMarker, -1, -1):
			#consider review of this block
			try:
				value = int(url[i])
				yearExtract = url[i] + yearExtract
			except ValueError:
				break

		yearExtract = yearExtract[0:4]
		return yearExtract

def extractYearFromUrlOld(url):
	if(len(url) > 0):
		
		#http://www.webarchive.org.uk:80/wayback/archive/20090101092312/http://www.google.com/
		lasIndexOfHTTPMarker = url.rfind("/http://")
		if lasIndexOfHTTPMarker<0:
			lasIndexOfHTTPMarker = url.rfind("/https://")
		lasIndexOfHTTPMarker = lasIndexOfHTTPMarker - 1
		yearExtract = ''

		for i in range(lasIndexOfHTTPMarker, -1, -1):
			#consider review of this block
			try:
				value = int(url[i])
				yearExtract = url[i] + yearExtract
			except ValueError:
				break

		yearExtract = yearExtract[0:4]
		return yearExtract

def getFolderNameFromUrlOld2(url):

	url = url.strip()
	folderName = ''
	if(len(url) > 0):
		url = url.lower()

		folderName = tldextract.extract(url)[0] + "." + tldextract.extract(url)[1] + "." + tldextract.extract(url)[2]

		if( folderName[0] == '.' ):
			folderName = 'www' + folderName

		'''
		urlPath = urlparse.urlparse(url)[2]
		# remove nonalphanuemeric
		urlPath = re.sub('[^0-9a-zA-Z]+', '-', urlPath)

		if( urlPath[-1] == '-' ):
			urlPath = urlPath[0:len(urlPath)-1]
		'''

	return folderName


#given this url: http://www.example.com, the folder name returned is example
def generateFolderNameFromUrlOld(url):

	if(len(url) > 0):

		indexOfHTTP = url.rfind(".")
		mementoGIFsPath = ''

		
		i = indexOfHTTP - 1
		while(i > -1):
			character = url[i]
			if(character.isalpha()):
				mementoGIFsPath = character + mementoGIFsPath
			else:
				break
			i = i-1
		
		if not os.path.exists(mementoGIFsPath):
			os.makedirs(mementoGIFsPath)


		return mementoGIFsPath

#given this url: http://www.example.com, the folder name returned is example
def generateFolderNameFromURLUsingHash(url):

	folderName = ''
	folderAlreadyExists = True

	url = url.strip()
	if(len(url) > 0):
		url = url.lower()
		
		canonicalURL = getCanonicalUrl(url)
		folderName = getHash(canonicalURL)

		if not os.path.exists(folderName):
			folderAlreadyExists = False
			os.makedirs(folderName)
		
	return folderName, folderAlreadyExists
	
def takeScreenshots(dictionaryOfItems, folderName, urlsFile, resolutionX = '1024', resolutionY = '768'):

	if( len(dictionaryOfItems)>0 ):

		phantomscript = os.path.join(os.path.dirname(__file__), globalPrefix+'webshots.js')
		sortedKeys = sorted(dictionaryOfItems.keys())

		#for yearKey, urlValue in dictionaryOfItems.items():
		for yearKey in sortedKeys:

			urlValue = dictionaryOfItems[yearKey]
			#yearValue = extractYearFromUrl(urlValue)
			#call(['phantomjs', phantomscript, urlValue, resolutionX, resolutionY, folderName, str(yearKey)])
			puppeteerScript = os.path.join(os.path.dirname(__file__), globalPrefix+'takeScreenshot.js')
			nodeSystemPath = getConfigParameters('nodeSystemPath')
			call([nodeSystemPath, puppeteerScript, urlValue, resolutionX, resolutionY, folderName, str(yearKey)])
			
			urlsFile.write(str(yearKey) + ': ' + urlValue + '\n')

		return True

	return False

def convertToAnimatedGIF(path):

	if( len(path)> 0 ):
		
		filenames = next(os.walk('./' + path + '/'))[2]

		for f in filenames:

			if(f.find(".png")>0):
				params = [ 'convert',
							'./'+ path+ '/' + f,
							'-pointsize',
							'50',
							'label:'+ f.replace(".png",""),
							'+swap',
		          			'-gravity',
		          			'Center',
		          			'-append',
		          			'-frame',
		          			'10',
		          			'./'+ path+ '/' + f
		          		]
				subprocess.check_call(params)

		params = ['convert', './'+path+'/*.png', './'+path+'/'+path+'Fast.gif']
		subprocess.check_call(params)
		params = ['convert', '-delay', '400','./'+path+'/*.png', './'+path+'/'+path+'Delay4.gif']
		subprocess.check_call(params)
     
def optimizeGifs(folderName):

	if(len(folderName) > 0):

		os.chdir(folderName)
		for file in glob.glob("*.gif"):

			indexOfMarker = file.find("Delay")
			if(indexOfMarker > -1):

				newfile = file[:indexOfMarker] + 'Opt' + file[indexOfMarker:]
				#optimize
				params = ['../gifsicle-static','--lossy=80', '--optimize', '--colors', '160', '--resize-width', '800', '-o', newfile, file]
				subprocess.check_call(params)

				return newfile

def generateMP4(folderName, beginYear):
	if(len(folderName) > 0):
		os.chdir(folderName)
		params = ['ffmpeg', '-r', '1', '-start_number', beginYear '-i', '%d.png', '-s', '864x1080', '-pix_fmt', 'yuv420p', '-vcodec', 'libx264', folderName+'.mp4']
		subprocess.check_call(params)

def timelapse(url, screen_name = '', tweetID = ''):

	someThingWentWrongFlag = False
	if(len(url) > 0):
		url = url.lower()
		mementoGIFsPath, folderAlreadyExists = generateFolderNameFromURLUsingHash(url)

		#if folder exists exit - start

		if( folderAlreadyExists ):
			print('... folder already exists, exiting')
			return False

		#if folder exists exit - end

		if(len(mementoGIFsPath) > 0):

			try:

				possibleFolderNameToDelete = os.getcwd() + '/' + mementoGIFsPath + '/'

				print("...opening urlsFile.txt")
				urlsFile = open("./" + mementoGIFsPath + "/urlsFile.txt", "w")

				# scrutiny - start
				print("...getting memento pages")
				pages = getMementosPages(url)
				print("...done getting memento pages")
				
				mementosList = []
				for i in range(0,len(pages)):
					mementos = getItemGivenSignature(pages[i])
					mementosList.append(mementos)
				# scrutiny - end


				yearUrlDictionary = get1MementoPerYear(mementosList, globalMementoUrlDateTimeDelimeter)

				#sort by date
				#this does not seem to return dictionary, list instead
				sortedKeysOfYearUrlDictionary = sorted(yearUrlDictionary.keys())
				
				
				lengthOfYearUrlDictionary = len(yearUrlDictionary)
				if( lengthOfYearUrlDictionary > 0 ):

					beginYear = str(sortedKeysOfYearUrlDictionary[0]) 
					endYear = str(sortedKeysOfYearUrlDictionary[len(sortedKeysOfYearUrlDictionary)-1])
					
					urlsFile.write("What Did " + url + " Look Like From " + beginYear + " To " + endYear + "?\n\n")
					urlsFile.write("Links" + ":\n")
					


				#print len(yearUrlDictionary), " years "

				#for year,url in yearUrlDictionary.items():
				#	print year, ",", url

			
				print("...taking screenshots")
				result = takeScreenshots (yearUrlDictionary, mementoGIFsPath, urlsFile)
				print("...done taking screenshots")

				print("...done opening urlsFile.txt")
				urlsFile.close()

				
				if(result):
					print("...labelling screenshots and converting to gif")
					convertToAnimatedGIF(mementoGIFsPath)
					print("...done labelling screenshots and converting to gif")
					print("...optimizing Gifs")
					optimizeGifs(mementoGIFsPath)
					print("...done optimizing Gifs")
					print("...creating mp4 file")
					generateMP4(mementoGIFsPath, beginYear)
					print("...done creating mp4 file")

					'''
					#this block has been deprecated - start
					print "...prepending " + globalDataFileName + " with url: ", url

					tumblrDataFile = open(globalDataFileName, 'r')
					tumblrDataFileLines = tumblrDataFile.readlines()
					tumblrDataFile.close()

					tumblrDataFile = open(globalDataFileName, 'w')

					if( len(screen_name)>0 and len(tweetID)>0 ):
						screen_name = screen_name.strip()
						tweetID = tweetID.strip()
						tumblrDataFile.write(url + "," + " [tumblrUploadIDPlaceHolder], " + screen_name + ", " + tweetID + "\n")
					else:
						tumblrDataFile.write(url + "," + " [tumblrUploadIDPlaceHolder]\n")


					tumblrDataFile.writelines(tumblrDataFileLines)
					tumblrDataFile.close()
					print "...done appending " + globalDataFileName + " with url"
					#this block has been deprecated - end
					'''
				else:
					print('...deleting empty bad result:', possibleFolderNameToDelete)
					#someThingWentWrongFlag = True could mean that the request to the server was not successful,
					#but could be successful in the future
					someThingWentWrongFlag = True
					co = 'rm -r ' + possibleFolderNameToDelete
					
					subprocess.getoutput(co)

					
			


			except:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print((fname, exc_tb.tb_lineno, sys.exc_info() ))
				#urlsFile.close()
				#tumblrDataFile.close()

				errorMessage = (fname, exc_tb.tb_lineno, sys.exc_info() )
				#mod1
				sendErrorEmail( str(errorMessage) )
	else:
		print("Url length error: Url length must be greater than zero")

	return someThingWentWrongFlag

def main():
	if len(sys.argv) == 1:
		print("Usage: ", sys.argv[0] + " url (e.g: " + sys.argv[0] + " http://www.example.com)")
		return
	elif len(sys.argv) == 2:
		timelapse(sys.argv[1])

		'''
		pages = getMementosPages(sys.argv[1])
		mementosList = []
		for i in range(0,len(pages)):
			mementos = getItemGivenSignature(pages[i])
			mementosList.append(mementos)

		yearUrlDictionary = get1MementoPerYear(mementosList, globalMementoUrlDateTimeDelimeter)
		for year, Url in yearUrlDictionary.items():
			print year, Url
		'''
		

	#elif block deprecated
	#elif len(sys.argv) == 3:
	#	timelapse(sys.argv[1], sys.argv[2])
	
#'http://timetravel.mementoweb.org/timemap/link/http://www.timeout.com/london'
if __name__ == "__main__":
	main()
	


'''

#params = [ 'convert',
		#				'./'+ path+ '/' + f,
		#				'-pointsize',
		#				'50',
		#				'label:'+ f.replace(".png",""),
		#				'+swap',
	    #      			'-gravity',
	    #      			'Center',
	    #      			'-append',
	    #      			'-frame',
	    #      			'10',
	    #      			'./'+ path+ '/' + f
	    #      		]

'''