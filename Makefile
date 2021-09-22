.PHONY: test build

install:
	poetry install

build:
	mkdir -p build/contracts
	ligo compile contract ./contracts/tezos/fa2_vault.ligo --output-file ./build/contracts/fa2_vault.tz -e main
	ligo compile contract ./contracts/tezos/fa12_vault.ligo --output-file ./build/contracts/fa12_vault.tz -e main
	cp ./contracts/tezos/tez_vault.tz ./build/contracts/

test:
	pytest . -v
