import os, sys
from timelapse import timelapse
from getConfig import getConfigParameters

globalPrefix = getConfigParameters('globalPrefix')
globalInputUrlsFileName = globalPrefix + 'twitter_requests_wdill.txt'
try:

	listOfNominatedURLs = open(globalInputUrlsFileName, "r")
	nominationTuples = listOfNominatedURLs.readlines()

except:
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	print((fname, exc_tb.tb_lineno, sys.exc_info() ))
	listOfNominatedURLs.close()


print("read lines: ", len(nominationTuples))
originalPath = os.getcwd()

for i in range(0,len(nominationTuples)):

	#<0: URL, 1: SCREEN-NAME, 2: DATE-TIME, 3: TWEET-ID, 4: (optional POST-ID, 5: POST-FLAG) >
	nominationData = nominationTuples[i].split(' <> ')
	
	#this url has not been published
	if( len(nominationData) < 5):

		URL = nominationData[0].strip()
		#screen_name = nomimationData[1].strip()
		#datetime = nomimationData[2].strip()
		#tweetID = nomimationData[3].strip()

		os.chdir(originalPath)
		print("...sending ", URL, " to timelapse to take pictures")
		timelapse(URL)

print('...calling timelapseSubEngine.py')
#MOD
os.chdir(originalPath)
pythonVirtualEnvPath = getConfigParameters('pythonVirtualEnv1Path')
os.system(pythonVirtualEnvPath + ' ' + globalPrefix + 'timelapseSubEngine.py &')