.PHONY: test

install:
	poetry install

build:
	mkdir -p bin/tezos
	mkdir -p bin/ethereum
	for f in contracts/tezos/*.ligo; do docker run -v $(PWD):$(PWD) ligolang/ligo:0.24.0 compile-contract $(PWD)/$$f main > bin/tezos/$$(basename $${f%.ligo}).tz; done

test:
	pytest . -v
