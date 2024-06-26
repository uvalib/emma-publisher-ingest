//
//
//

// include this on a cmdline build only
//go:build cmdline

package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {

	//var messageId string
	var messageId string
	var source string
	var bucket string
	var key string

	flag.StringVar(&messageId, "messageid", "0-0-0-0", "Message identifier")
	flag.StringVar(&source, "source", "the.source", "Message source")
	flag.StringVar(&bucket, "bucket", "", "Bucket name")
	flag.StringVar(&key, "key", "", "Key name")
	flag.Parse()

	if len(key) == 0 {
		fmt.Printf("ERROR: incorrect commandline, use --help for details\n")
		os.Exit(1)
	}

	if len(bucket) == 0 {
		fmt.Printf("INFO: Bucket is blank. Now looking for a local file with key name.\n")

	}

	err := process(messageId, source, bucket, key)
	if err != nil {
		fmt.Printf("ERROR: %s\n", err.Error())
		os.Exit(1)
	}

	fmt.Printf("INFO: terminating normally\n")
}

//
// end of file
//
