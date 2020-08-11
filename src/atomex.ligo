type txParam is list (address * (nat * nat));
type transferParam is list (address * txParam);

type tokenLeg is record
  tokenId: nat;
  amount: nat;
end

type initiateParam is record
  hashedSecret: bytes;
  participant: address;
  refundTime: timestamp;
  transferEntry: contract(transferParam);
  legs: list (tokenLeg);
end

type parameter is 
  | Initiate of initiateParam
  | Redeem of bytes
  | Refund of bytes

type swapState is record
  initiator: address;
  participant: address;
  refundTime: timestamp;
  tokenAddress: address;
  legs: list (tokenLeg);
end

type storage is big_map(bytes, swapState);

function getSwapState(const hashedSecret: bytes; const s: storage) : swapState is
  case s[hashedSecret] of
    | Some(state) -> state
    | None -> (failwith("no swap for such hash") : swapState)
  end; attributes ["inline"];

function getTransferEntry(const tokenAddress: address) : contract(transferParam) is
  case (Tezos.get_contract_opt(tokenAddress) : option(contract(transferParam))) of
    | Some(entry) -> entry
    | None -> (failwith("expected transfer entrypoint") : contract(transferParam))
  end; attributes ["inline"];

function transfer(const transferEntry: contract(transferParam);
                  const src: address;
                  const dst: address; 
                  const legs: list (tokenLeg)) : operation is
  block {
    const dstBulk : list (address * (nat * nat)) = List.map (
      function (const leg : tokenLeg) : (address * (nat * nat)) is (dst, (leg.tokenId, leg.amount)), 
      legs);
    const params: transferParam = list[(src, dstBulk)];
    const op: operation = Tezos.transaction(params, 0tz, transferEntry);
  } with op; attributes ["inline"];

function doInitiate(const initiate: initiateParam; var s: storage) : (list(operation) * storage) is 
  block {
    if (initiate.refundTime <= now) then failwith("refund time has already come"); else skip;
    if (32n =/= Bytes.length(initiate.hashedSecret)) then failwith("hash size doesn't equal 32 bytes"); else skip;
    if (Tezos.source = initiate.participant) then failwith("SOURCE cannot act as participant"); else skip;
    if (Tezos.sender = initiate.participant) then failwith("SENDER cannot act as participant"); else skip;

    const state: swapState = 
      record [
        initiator = Tezos.sender;
        participant = initiate.participant;
        refundTime = initiate.refundTime;
        tokenAddress = Tezos.address(initiate.transferEntry);
        legs = initiate.legs;
      ];

    case s[initiate.hashedSecret] of
      | None -> s[initiate.hashedSecret] := state
      | Some(x) -> failwith("swap for this hash is already initiated")
    end;

    const depositTx: operation = transfer(
      initiate.transferEntry, Tezos.sender, Tezos.self_address, initiate.legs);
  } with (list[depositTx], s)

function doRedeem(const secret: bytes; var s: storage) : (list(operation) * storage) is
  block {
    if (32n =/= Bytes.length(secret)) then failwith("secret size doesn't equal 32 bytes"); else skip;
    const hashedSecret: bytes = Crypto.sha256(Crypto.sha256(secret));
    const swap: swapState = getSwapState(hashedSecret, s);
    if (now >= swap.refundTime) then failwith("refund time has already come"); else skip;

    remove hashedSecret from map s;

    const transferEntry: contract(transferParam) = getTransferEntry(swap.tokenAddress);
    const redeemTx: operation = transfer(transferEntry, Tezos.self_address, swap.participant, swap.legs);
  } with (list[redeemTx], s) 

function doRefund(const hashedSecret: bytes; var s: storage) : (list(operation) * storage) is
  block {
    const swap: swapState = getSwapState(hashedSecret, s);
    if (now < swap.refundTime) then failwith("refund time hasn't come"); else skip;

    remove hashedSecret from map s;

    const transferEntry: contract(transferParam) = getTransferEntry(swap.tokenAddress);
    const refundTx: operation = transfer(transferEntry, Tezos.self_address, swap.initiator, swap.legs);
  } with (list[refundTx], s) 

function main (const p: parameter; var s: storage) : (list(operation) * storage) is
block {
  if 0tz =/= Tezos.amount then failwith("this contract does not accept tez"); else skip;
} with case p of
  | Initiate(initiate) -> (doInitiate(initiate, s))
  | Redeem(redeem) -> (doRedeem(redeem, s))
  | Refund(refund) -> (doRefund(refund, s))
end