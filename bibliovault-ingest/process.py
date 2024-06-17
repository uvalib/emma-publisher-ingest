#
#
#

import boto3

def process(bucket, key):

	print( "EVENT: " + bucket + "/" + key + "\n" )

	s3 = boto3.resource('s3')

        # download the file
	print("DEBUG: downloading s3://" + bucket + "/" + key + ":\n")
	response = s3.Object(bucket, key).get()
	buf = response['Body'].read()

        # do the processing

	# all is well
	return None

#
# end of file
#
