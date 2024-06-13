package main

import (
	"fmt"
	"os"
	"strconv"
)

// Config defines all of the service configuration parameters
type Config struct {
	// upload configuration
	BucketName        string // the bucket name
	BucketKeyTemplate string // the bucket key template
}

func envWithDefault(env string, defaultValue string) string {
	val, set := os.LookupEnv(env)

	if set == false {
		fmt.Printf("INFO: environment variable not set: [%s] using default value [%s]\n", env, defaultValue)
		return defaultValue
	}

	return val
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

func envToInt(env string) (int, error) {

	number, err := ensureSetAndNonEmpty(env)
	if err != nil {
		return -1, err
	}

	n, err := strconv.Atoi(number)
	if err != nil {
		return -1, err
	}
	return n, nil
}

// loadConfiguration will load the service configuration from env/cmdline
// and return a pointer to it. Any failures are fatal.
func loadConfiguration() (*Config, error) {

	var cfg Config

	var err error
	cfg.BucketName, err = ensureSetAndNonEmpty("BUCKET_NAME")
	if err != nil {
		return nil, err
	}
	cfg.BucketKeyTemplate, err = ensureSetAndNonEmpty("BUCKET_KEY_TEMPLATE")
	if err != nil {
		return nil, err
	}

	fmt.Printf("[conf] BucketName        = [%s]\n", cfg.BucketName)
	fmt.Printf("[conf] BucketKeyTemplate = [%s]\n", cfg.BucketKeyTemplate)

	return &cfg, nil
}
