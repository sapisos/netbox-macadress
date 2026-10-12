sources = netbox_macadress

.PHONY: format lint pre-commit clean

format:
	ruff check --select I --fix $(sources)
	ruff format $(sources)

lint:
	ruff check $(sources)

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf *.egg-info
	rm -rf .tox dist site
