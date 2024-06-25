#
#
#

import argparse

from handler import *

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--bucket', dest='bucket', type=str, help='Bucket name')
	parser.add_argument('--key', dest='key', type=str, help='Key name')
	args = parser.parse_args()

	# payload is an array of records containing the body sent to the queue
	payload = {
		"Records": [
			{ "body": {"bucket": args.bucket, "key": args.key}}
		]
	}

	# process
	err = lambda_handler(payload, None)

if __name__ == "__main__":
    main()

#
# end of file
#
