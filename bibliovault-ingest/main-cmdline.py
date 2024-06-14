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

        # events are dictionaries
	event = {
		"bucket": args.bucket,
		"key": args.key
	}

	err = lambda_handler(event, None)

if __name__ == "__main__":
    main()

#
# end of file
#
