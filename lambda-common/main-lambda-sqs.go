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

	// loop through possible messages
	for _, message := range sqsEvent.Records {
		// convert to an eventbus event
		var mbEvent events.EventBridgeEvent
		err := json.Unmarshal([]byte(message.Body), &mbEvent)
		if err != nil {
			fmt.Printf("ERROR: unmarshaling event bridge event (%s), continuing\n", err.Error())
			returnErr = err
			continue
		}

		// process the message, in the event of an error, it is re-queued
		err = process(mbEvent.ID, mbEvent.Source, mbEvent.Detail)
		if err != nil {
			fmt.Printf("ERROR: processing event bridge event (%s), continuing\n", err.Error())
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
