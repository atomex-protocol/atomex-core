var Atomex = artifacts.require("../contracts/ethereum/AtomexErc20Vault.sol");

module.exports = function(deployer) {
  deployer.deploy(Atomex);
};
