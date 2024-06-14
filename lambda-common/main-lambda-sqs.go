//
// main for lambda deployable
//

// include this on a lambda build only
//go:build lambda

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

func HandleRequest(ctx context.Context, sqsEvent events.SQSEvent) error {

	var returnErr error

	// loop through possible SQS event records
	for _, sqsEv := range sqsEvent.Records {

		// convert to an S3 event
		var s3Event events.S3Event
		err := json.Unmarshal([]byte(sqsEv.Body), &s3Event)
		if err != nil {
			fmt.Printf("ERROR: unmarshaling S3 event (%s), continuing\n", err.Error())
			returnErr = err
			continue
		}

		// loop through possible S3 event records
		for _, s3Ev := range s3Event.Records {

			source := s3Ev.EventSource
			bucket := s3Ev.S3.Bucket.Name
			key := s3Ev.S3.Object.Key

			// process the message, in the event of an error, it is re-queued
			err = process(sqsEv.MessageId, source, bucket, key)
			if err != nil {
				fmt.Printf("ERROR: processing S3 event (%s), continuing\n", err.Error())
				returnErr = err
			}
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
