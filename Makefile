.PHONY: test

compile:
	for f in contracts/tezos/*.ligo; do docker run -v $(PWD):$(PWD) ligolang/ligo:0.16.1 compile-contract $(PWD)/$$f main > $(PWD)/$${f%.ligo}.tz; done
	ls -al contracts/tezos/*.tz

test:
	pytest . -v
