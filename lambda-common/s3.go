//
// simple module to get and set parameter values in the ssm
//

package main

import (
	"bytes"
	"context"
	"fmt"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"io"
)

func newS3Client() (*s3.Client, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return nil, err
	}
	return s3.NewFromConfig(cfg), nil
}

func getS3(client *s3.Client, bucket string, key string) ([]byte, error) {

	fmt.Printf("DEBUG: downloading s3://%s/%s\n", bucket, key)

	result, err := client.GetObject(context.TODO(), &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})

	if err != nil {
		return nil, err
	}
	defer result.Body.Close()

	buf, err := io.ReadAll(result.Body)
	return buf, nil
}

func putS3(client *s3.Client, bucket string, key string, buffer []byte) error {

	fmt.Printf("DEBUG: uploading s3://%s/%s\n", bucket, key)

	_, err := client.PutObject(context.TODO(),
		&s3.PutObjectInput{
			Bucket: aws.String(bucket),
			Key:    aws.String(key),
			Body:   bytes.NewReader(buffer),
		})

	if err != nil {
		return err
	}

	return nil
}

//
// end of file
//
