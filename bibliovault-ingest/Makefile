PIPBIN = pip3
DEPLOYDIR = package

build: deployable

linux: deployable

all: deployable

deployable:
	rm -rf $(DEPLOYDIR)
	mkdir $(DEPLOYDIR)
	$(PIPBIN) install --target $(DEPLOYDIR) boto3
	cp handler.py $(DEPLOYDIR)
	cd $(DEPLOYDIR); zip -r deployment.zip *

clean:
	rm -rf $(DEPLOYDIR)
