#
#
#

import json

from process import *

def lambda_handler(payload, context):

	if payload:
		print( "RECV [" + str(payload) + "]\n" )

		# convert to json
		pl = json.loads(payload)

		# extract the record and process
		body = pl["Records"][0]["body"]
		return process( body["bucket"], body["key"])

	# all is well
	return None

#
# end of file
#
