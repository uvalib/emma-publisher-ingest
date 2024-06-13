GOCMD = go
GOBUILD = $(GOCMD) build
GOCLEAN = $(GOCMD) clean
GOTEST = $(GOCMD) test
GOGET = $(GOCMD) get
GOMOD = $(GOCMD) mod
GOFMT = $(GOCMD) fmt
GOVET = $(GOCMD) vet
BINNAME = cmd
COMMON = ../lambda-common
DEPLOYNAME = bootstrap

build: common cmdline

linux: common deployable

all: cmdline deployable

cmdline:
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 $(GOBUILD) -tags cmdline -o bin/$(BINNAME)

deployable:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) -tags lambda.norpc,lambda -o bin/$(DEPLOYNAME)
	cd bin; zip deployment.zip $(DEPLOYNAME)

common:
	-ln -s $(COMMON)/main-cmdline.go . 2> /dev/null || true
	-ln -s $(COMMON)/main-lambda-sqs.go . 2> /dev/null || true
	-ln -s $(COMMON)/s3.go . 2> /dev/null || true

clean:
	$(GOCLEAN)
	rm -rf bin

dep:
	$(GOGET) -u
	$(GOMOD) tidy
	$(GOMOD) verify

fmt:
	$(GOFMT)

vet:
	$(GOVET)
