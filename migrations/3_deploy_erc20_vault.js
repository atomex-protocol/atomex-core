var Atomex = artifacts.require("../contracts/ethereum/Erc20Vault.sol");

module.exports = function(deployer) {
  deployer.deploy(Atomex);
};
