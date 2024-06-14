//
// main message processing
//

package main

import (
	"bytes"
	"encoding/json"
	"fmt"

	"github.com/antchfx/xmlquery"
)

type IngestFileNotification struct {
	Bucket string `json:"bucket"`
	Key    string `json:"key"`
}

func process(messageId string, messageSrc string, bucket string, key string) error {

	fmt.Printf("EVENT %s from:%s -> %s/%s\n", messageId, messageSrc, bucket, key)

	// load configuration
	cfg, err := loadConfiguration()
	if err != nil {
		return err
	}

	// init the S3 client
	s3, err := newS3Client()
	if err != nil {
		fmt.Printf("ERROR: creating S3 client (%s)\n", err.Error())
		return err
	}

	// init the SQS client
	sqs, err := newSqsClient()
	if err != nil {
		fmt.Printf("ERROR: creating SQS client (%s)\n", err.Error())
		return err
	}

	// download from S3
	buf, err := getS3(s3, bucket, key)
	if err != nil {
		fmt.Printf("ERROR: downloading (%s)\n", err.Error())
		return err
	}

	// process the buffer
	_, err = xmlquery.Parse(bytes.NewReader(buf))
	if err != nil {
		fmt.Printf("ERROR: parsing downloaded XML (%s)\n", err.Error())
		return err
	}

	// ensure the XML and corresponding files are good

	// upload notification to the outbound queue
	n := IngestFileNotification{Bucket: bucket, Key: key}
	b, _ := json.Marshal(n)
	err = putSqs(sqs, cfg.OutQueue, b)
	if err != nil {
		fmt.Printf("ERROR: publishing (%s)\n", err.Error())
		return err
	}

	return nil
}

//
// end of file
//
