PIPBIN = pip3
DEPLOYDIR = package

build: deployable

linux: deployable

all: deployable

deployable:
	rm -rf $(DEPLOYDIR)
	mkdir $(DEPLOYDIR)
	$(PIPBIN) install --target $(DEPLOYDIR) cryptography==42.0.8 awscli==1.33.0 boto3==1.34.36 requests==2.31.0 requests-oauthlib pytz \
             jsonpath-ng jsonschema==4.6.1 internetarchive==3.6.0 iso-639 pyisbn botocore==1.34.118 certifi==2024.2.2 jmespath==1.0.1 \
             jsonpatch==1.33 jsonpointer==2.4 iso8601==2.1.0 opensearch==0.8 opensearch-dsl==2.0.1 aws-requests-auth==0.4.3 paramiko sshtunnel
	rm -fr $(DEPLOYDIR)/awscli/examples
	cp handler.py $(DEPLOYDIR)
	cp process.py $(DEPLOYDIR)
	cp -R internet_archive_shared  $(DEPLOYDIR)
	cp -R shared  $(DEPLOYDIR)
	cd $(DEPLOYDIR); zip -r deployment.zip * -x "**/__pycache__/*"

clean:
	rm -rf $(DEPLOYDIR)
