var Atomex = artifacts.require("../contracts/ethereum/AtomexEthVault.sol");

module.exports = function(deployer) {
  deployer.deploy(Atomex);
};
