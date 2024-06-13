//
//
//

// include this on a cmdline build only
//go:build cmdline

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/uvalib/librabus-sdk/uvalibrabus"
)

func main() {

	var messageId string
	var source string
	var eventName string
	var namespace string
	var objectId string
	var detail string
	var eventTime string

	flag.StringVar(&messageId, "messageid", "0-0-0-0", "Message identifier")
	flag.StringVar(&source, "source", "the.source", "Message source")
	flag.StringVar(&eventName, "eventname", "", "Event name")
	flag.StringVar(&namespace, "namespace", "", "Object namespace")
	flag.StringVar(&objectId, "objid", "", "Object identifier")
	flag.StringVar(&eventTime, "eventtime", "", "Time of the event")
	flag.StringVar(&detail, "detail", "", "Event detail, usually json")
	flag.Parse()

	if len(eventName) == 0 || len(namespace) == 0 || len(objectId) == 0 {
		fmt.Printf("ERROR: incorrect commandline, use --help for details\n")
		os.Exit(1)
	}

	ev := uvalibrabus.UvaBusEvent{}
	ev.EventName = eventName
	ev.Namespace = namespace
	ev.Identifier = objectId
	ev.EventTime = eventTime
	if len(detail) != 0 {
		ev.Detail = json.RawMessage(detail)
	}

	pl, _ := ev.Serialize()
	err := process(messageId, source, pl)
	if err != nil {
		fmt.Printf("ERROR: %s\n", err.Error())
		os.Exit(1)
	}

	fmt.Printf("INFO: terminating normally\n")
}

//
// end of file
//
