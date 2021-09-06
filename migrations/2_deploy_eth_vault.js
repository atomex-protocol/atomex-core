var Atomex = artifacts.require("../contracts/ethereum/EthVault.sol");

module.exports = function(deployer) {
  deployer.deploy(Atomex);
};
