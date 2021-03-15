import datetime
import sys, traceback


def countDots(inputString, signatureCharacter):

	countOfDots = 0
	if( len(inputString) > 0 and len(signatureCharacter) ):
		for i in range(0, len(inputString) ):
			if( inputString[i] == signatureCharacter ):
				countOfDots = countOfDots + 1

	return countOfDots


'''
check how many times this code has run today by counting dots:

The idea of this function is to limit the number of times the 
use code runs. If the use code specifies that is needs to run x (maximumRun = x) times,
the following happens:

Assume maximumRun = 3 (runs maximum of 3 times per day)
Same day
	The first time the code runs, runCount is empty so the date. at time of run is added to runCount (function returns true)
	The second time the code runs, runCount file: date.. (function returns true)
	The third time the code runs, runCount file: date... (function returns true)
	The fourth time, the does not run, runCount file: date.... (function returns false)
Different day
	This is considered a new run, so code runs, runCount file: date. (function returns true)

'''
def checkRunCount(maximumRun, signatureCharacter, runCountFileName):

	try:
		runFile = open(runCountFileName, 'r')
		lines = runFile.readlines()
		runFile.close()
	except:
		print(traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],limit=2,file=sys.stdout))
		continueFlag = False

	today = datetime.date.today()
	today = str(today)
	
	whatToWrite = ''
	continueFlag = False
	if( len(lines) == 0 ):
		#if file is empty
		whatToWrite = today + '.\n'
		continueFlag = True
	else:
		whatToWrite = lines[0]
		dateOfRun = lines[0].strip()

		if( dateOfRun.replace(signatureCharacter, '') == today ):
			#file has been written today, so append dot
			howManyRuns = countDots(dateOfRun, signatureCharacter)
			dateOfRun = dateOfRun + '.\n'
			whatToWrite = dateOfRun

			#this file has not exceeded quota
			if( howManyRuns < maximumRun ):
				continueFlag = True

		else:
			whatToWrite = today + '.\n'
			#file has not been written today
			continueFlag = True
			
	try:
		runFile = open(runCountFileName, 'w')
		runFile.write(whatToWrite)
		runFile.close()
	except:
		print(traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2],limit=2,file=sys.stdout))
		continueFlag = False

	return continueFlag