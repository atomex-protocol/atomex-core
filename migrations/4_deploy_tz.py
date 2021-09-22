from pytezos import ContractInterface, pytezos
import argparse
import os


def deploy_contract(filename, ptz):
    print(f'deploying {filename}...')
    with open(filename, 'r') as f:
        contract_michelson = f.read()

    contract = ContractInterface.from_michelson(contract_michelson)
    opg = ptz.origination(contract.script()).send(ttl=1)
    print(f'success: {opg.opg_hash}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy Atomex contracts to tezos')
    parser.add_argument('-n', type=str, help='node URL', required=True, default='https://rpc.tzkt.io/mainnet')
    parser.add_argument('-p', type=str, help='private key', required=True)
    args = parser.parse_args()

    if args.n == '':    
        raise argparse.ArgumentError(None, 'empty node URL')

    print(f'Node URL: {args.n}')
    if args.p == '':
        raise argparse.ArgumentError(None, 'empty private key')

    ptz = pytezos.using(shell=args.n, key=args.p)

    cwd = os.getcwd()
    files = [
        f'{cwd}/build/contracts/tez_vault.tz',
        f'{cwd}/build/contracts/fa12_vault.tz',
        f'{cwd}/build/contracts/fa2_vault.tz',
    ]

    for file in files:
        deploy_contract(file, ptz)
