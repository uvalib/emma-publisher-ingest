#
#
#

from process import process

def lambda_handler(event, context):

    # return status
    ret = None

    if event:
        print( "RECV [" + str(event) + "]\n" )

        for record in event["Records"]:
            # extract the record and process
            body = eval(record["body"])
            val = process( body["bucket"], body["key"])
            if val:
                ret = val

    return ret

#
# end of file
#
