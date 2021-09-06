var Migrations = artifacts.require("../contracts/ethereum/Migrations.sol");

module.exports = function(deployer) {
  deployer.deploy(Migrations);
};
