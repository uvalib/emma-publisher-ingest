//
// main message processing
//

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/antchfx/xmlquery"
)

// IngestFileNotification holds info for the ingest step
type IngestFileNotification struct {
	Bucket string `json:"bucket"`
	Key    string `json:"key"`
}

func process(messageID string, messageSrc string, bucket string, key string) error {

	fmt.Printf("EVENT %s from:%s -> %s/%s\n", messageID, messageSrc, bucket, key)

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
	buf := []byte{}

	// get the file content

	if len(bucket) == 0 {
		buf, err = os.ReadFile(key)
		if err != nil {
			fmt.Printf("ERROR: reading local file %s (%s)\n", key, err.Error())
		}
		bucket = "bibliovault-transfer-staging"

	} else {
		// download from S3
		buf, err = getS3(s3, bucket, key)
		if err != nil {
			fmt.Printf("ERROR: downloading (%s)\n", err.Error())
			return err
		}

	}

	// process the buffer
	onix, err := xmlquery.Parse(bytes.NewReader(buf))
	if err != nil {
		fmt.Printf("ERROR: parsing downloaded XML (%s)\n", err.Error())
		return err
	}

	// ensure the XML and corresponding files are good

	idList, err := xmlquery.QueryAll(onix, "//RecordReference")
	errorCount := 0

	for i, v := range idList {
		id, _ := strings.CutPrefix(v.InnerText(), "org.bibliovault.")
		filename := fmt.Sprintf("%s.epub", id)

		if fileHead, err := headS3(s3, bucket, filename); err == nil {
			fmt.Printf("INFO: found %+v \n", fileHead)

		} else {
			fmt.Printf("ERROR: %s/%s - %s\n", bucket, filename, err.Error())
			errorCount = errorCount + 1
		}

		fmt.Printf("%d: %s\n", i, id)
	}
	fmt.Printf("INFO: processed %d records\n", len(idList))

	if errorCount > 0 {
		return fmt.Errorf("%d files are missing. Not continuing with ingest", errorCount)
	}

	// upload notification to the outbound queue
	fmt.Printf("INFO: validation complete, sending notification to: %s", cfg.OutQueue)
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
