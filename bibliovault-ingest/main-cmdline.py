#
#
#

from handler import *

def main():
        # events are dictionaries
	event = {
		"id": "123456",
		"year": 2024
	}
	context = None
	err = lambda_handler(event, context)

if __name__ == "__main__":
    main()

#
# end of file
#
