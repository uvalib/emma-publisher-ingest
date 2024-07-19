PIPBIN = pip3
DEPLOYDIR = package

build: deployable

linux: deployable

all: deployable

deployable:
	rm -rf $(DEPLOYDIR)
	mkdir $(DEPLOYDIR)
	$(PIPBIN) install --target $(DEPLOYDIR) boto3==1.34.36 requests==2.31.0 requests-oauthlib pytz jsonpath-ng jsonschema==4.6.1
	$(PIPBIN) install --target $(DEPLOYDIR) internetarchive==3.6.0 iso-639 pyisbn botocore==1.34.60 certifi==2024.2.2 
	$(PIPBIN) install --target $(DEPLOYDIR) jmespath==1.0.1 jsonpatch==1.33 jsonpointer==2.4 iso8601==2.1.0 
	$(PIPBIN) install --target $(DEPLOYDIR) opensearch==0.8 opensearch-dsl==2.0.1 aws-requests-auth==0.4.3
	cp handler.py $(DEPLOYDIR)
	cp process.py $(DEPLOYDIR)
	cp -R bibliovault_shared  $(DEPLOYDIR)
	cp -R ingestion_handler  $(DEPLOYDIR)
	cp -R shared  $(DEPLOYDIR)
	cp ingestion-record.schema.json $(DEPLOYDIR)
	cd $(DEPLOYDIR); zip -r deployment.zip *

clean:
	rm -rf $(DEPLOYDIR)
