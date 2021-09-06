install:
	yarn
	poetry install

build:
	for f in contracts/tezos/*.ligo; do docker run -v $(PWD):$(PWD) ligolang/ligo:0.16.1 compile-contract $(PWD)/$$f main > $(PWD)/$${f%.ligo}.tz; done

test:
	pytest . -v
