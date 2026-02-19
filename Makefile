# Root Makefile — delegates to sub-projects

.PHONY: test-webapp lint-webapp format-webapp precommit-webapp
.PHONY: deploy-operator undeploy-operator
.PHONY: build-keip-integration

# Webapp targets
test-webapp:
	$(MAKE) -C webapp test

lint-webapp:
	$(MAKE) -C webapp lint

format-webapp:
	$(MAKE) -C webapp format

precommit-webapp:
	$(MAKE) -C webapp precommit

# Operator targets
deploy-operator:
	$(MAKE) -C operator deploy

undeploy-operator:
	$(MAKE) -C operator undeploy

# Integration app targets
build-keip-integration:
	cd keip-integration && mvn clean install
