PYTHON := pipenv run python
bot_version := $(shell pipenv run python python/setup.py --version)
dar := target/artifacts/hello-cdm.dar
bot := target/artifacts/hello-cdm-$(bot_version).tar.gz

.PHONY: package
package: $(bot) $(dar)


$(dar):
	daml build -o $@


$(bot):
	cd python && $(PYTHON) setup.py sdist
	rm -fr python/hello_cdm.egg-info
	mkdir -p $(@D)
	mv python/dist/hello-cdm-$(bot_version).tar.gz $@
	rm -r python/dist


.PHONY: clean
clean:
	rm -fr python/hello_cdm.egg-info python/dist target
