#
#
#

from process import *

def lambda_handler(event, context):

	if event:
		print( "RECV [" + str(event) + "]\n" )
		return process( event["bucket"], event["key"])

	# all is well
	return None

#
# end of file
#
