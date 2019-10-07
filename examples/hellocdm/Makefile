PYTHON := pipenv run python3
bot_version := $(shell python3 python/setup.py --version)
dar := target/artifacts/hello-cdm.dar
bot := target/artifacts/hello-cdm-$(bot_version).tar.gz

.PHONY: package
package: $(bot) $(dar)


$(dar):
	daml build -o $@


$(bot):
	cd python && python3 setup.py sdist
	rm -fr python/hello_cdm.egg-info
	mkdir -p $(@D)
	mv python/dist/hello-cdm-$(bot_version).tar.gz $@
	rm -r python/dist


.PHONY: clean
clean:
	rm -fr python/hello_cdm.egg-info python/dist target
