#
#
#

from process import *

def lambda_handler(event, context):

	if event:
		print( "RECV [" + str(event) + "]\n" )

		for record in event["Records"]:
			# extract the record and process
			body = record["body"]
			print( "REC: " + body["bucket"] + "/" + body["key"] + "\n")
		#return process( body["bucket"], body["key"])

	# all is well
	return None

#
# end of file
#
