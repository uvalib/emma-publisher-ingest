package main

import (
	"fmt"
	"os"
)

// Config defines all of the service configuration parameters
type Config struct {
	OutQueue string // the outbound queue name
}

func ensureSet(env string) (string, error) {
	val, set := os.LookupEnv(env)

	if set == false {
		err := fmt.Errorf("environment variable not set: [%s]", env)
		fmt.Printf("ERROR: %s\n", err.Error())
		return "", err
	}

	return val, nil
}

func ensureSetAndNonEmpty(env string) (string, error) {
	val, err := ensureSet(env)
	if err != nil {
		return "", err
	}

	if val == "" {
		err := fmt.Errorf("environment variable is empty: [%s]", env)
		return "", err
	}

	return val, nil
}

// loadConfiguration will load the service configuration from env/cmdline
// and return a pointer to it. Any failures are fatal.
func loadConfiguration() (*Config, error) {

	var cfg Config

	var err error
	cfg.OutQueue, err = ensureSetAndNonEmpty("OUT_QUEUE")
	if err != nil {
		return nil, err
	}

	fmt.Printf("[conf] OutQueue = [%s]\n", cfg.OutQueue)

	return &cfg, nil
}
