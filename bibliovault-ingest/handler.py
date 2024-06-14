#
#
#

def lambda_handler(event, context):

	if event:

		for record in event["Records"]:
			print( record )

	return nil

#
# end of file
#
