# Root Makefile — delegates to sub-projects

.PHONY: test-webapp lint-webapp format-webapp precommit-webapp
.PHONY: deploy-operator undeploy-operator
.PHONY: build-minimal-app

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

# Minimal app targets
build-minimal-app:
	cd minimal-app && mvn clean install
