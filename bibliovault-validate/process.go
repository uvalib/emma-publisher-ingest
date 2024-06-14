//
// main message processing
//

package main

import (
	"fmt"
)

func process(messageSrc string, bucket string, key string) error {

	fmt.Printf("EVENT from:%s -> %s/%s\n", messageSrc, bucket, key)

	// load configuration
	//cfg, err := loadConfiguration()
	//if err != nil {
	//	return err
	//}

	// init the S3 client
	//s3, err := newS3Client()
	_, err := newS3Client()
	if err != nil {
		fmt.Printf("ERROR: creating S3 client (%s)\n", err.Error())
		return err
	}

	// upload to S3
	//err = putS3(s3, cfg.BucketName, bucketKey, buf)
	//if err != nil {
	//	fmt.Printf("ERROR: uploading (%s)\n", err.Error())
	//	return err
	//}

	return nil
}

//
// end of file
//
