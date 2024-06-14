//
// main for lambda deployable
//

// include this on a lambda build only
//go:build lambda

package main

import (
	"context"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

func HandleRequest(ctx context.Context, event events.S3Event) error {

	var returnErr error

	// loop through possible event records
	for _, eventRecord := range event.Records {
		// process the message, in the event of an error, it is re-queued
		err := process(eventRecord.EventSource, eventRecord.S3.Bucket.Name, eventRecord.S3.Object.Key)
		if err != nil {
			fmt.Printf("ERROR: processing S3 event (%s), continuing\n", err.Error())
			returnErr = err
		}
	}

	return returnErr
}

func main() {
	lambda.Start(HandleRequest)
}

//
// end of file
//
