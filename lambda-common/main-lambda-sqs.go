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

func HandleRequest(ctx context.Context, event events.S3Event) error {

	var returnErr error

	// loop through possible messages
	for _, message := range event.Records {
		// convert to an S3 event
		var s3Event events.S3EventRecord
		err := json.Unmarshal([]byte(message.Body), &s3Event)
		if err != nil {
			fmt.Printf("ERROR: unmarshaling S3 event (%s), continuing\n", err.Error())
			returnErr = err
			continue
		}

		// process the message, in the event of an error, it is re-queued
		bucket := s3Event.S3.Bucket.Name
		key := s3Event.S3.Object.Key
		err = process(s3Event.Source, bucket, key)
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
