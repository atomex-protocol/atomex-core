-include .env
export $(shell sed 's/=.*//' .env)

.PHONY: test build deploy_tezos

install:
	poetry install

build:
	ligo compile contract ./contracts/tezos/fa2_vault.ligo --output-file ./build/contracts/fa2_vault.tz -e main
	ligo compile contract ./contracts/tezos/fa12_vault.ligo --output-file ./build/contracts/fa12_vault.tz -e main
	cp ./contracts/tezos/tez_vault.tz ./build/contracts/

test:
	pytest . -v

deploy_tezos:
	python ./migrations/4_deploy_tz.py -p ${TEZOS_PRIVATE} -n https://rpc.tzkt.io/mainnet
