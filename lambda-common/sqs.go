//
// simple module to get and set parameter values in the ssm
//

package main

import (
	"context"
	"encoding/json"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
)

func newSqsClient() (*sqs.Client, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return nil, err
	}
	return sqs.NewFromConfig(cfg), nil
}

func putSqs(client *sqs.Client, queueURL string, message json.RawMessage) error {

	_, err := client.SendMessage(context.TODO(), &sqs.SendMessageInput{
		QueueUrl:    aws.String(queueURL),
		MessageBody: aws.String(string(message)),
	})

	if err == nil {
		return err
	}

	return nil
}

//
// end of file
//
