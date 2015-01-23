import smtplib
import sys, traceback
from getConfig import getConfigParameters


def sendErrorEmail(errorMessage, subject='Error Message'):

    sender = getConfigParameters('senderEmail')
    recipientsCommaDelimited = getConfigParameters('receiversEmail')
    recipientsCommaDelimited = recipientsCommaDelimited.split(', ')

    if( len(errorMessage) > 0 and len(subject) > 0 and len(recipientsCommaDelimited) > 0 and len(sender) > 0 ):
        
        #mod1
        sendEmail(sender, recipientsCommaDelimited, subject, errorMessage)

def sendEmail(sender, receiversArray, subject, message):

	mailServer = getConfigParameters('mailServer')
	if(len(sender) > 0 and len(receiversArray) > 0 and len(subject) and len(message) > 0 and len(mailServer) > 0 ):

		toString = ''
		for email in receiversArray:
			toString = toString + ',' + email

		toString = toString[1:]
		message = 'From:' + sender + '\n' + 'To:' + toString + '\n' + 'Subject:' + subject + '\n\n' + message;

		#print 'toString:', toString
		#print ''
		#print 'message:', message

		try:
		   smtpObj = smtplib.SMTP(mailServer)
		   smtpObj.sendmail(sender, receiversArray, message)         
		   print "Successfully sent email"
		except:
		   print "Error: unable to send email"
		   print traceback.print_exception(sys.exc_type, sys.exc_value, sys.exc_traceback,limit=2,file=sys.stdout)
