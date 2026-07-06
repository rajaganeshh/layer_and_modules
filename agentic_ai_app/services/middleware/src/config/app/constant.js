const { randomInt } = require("node:crypto");

module.exports = {
  randomNumber: randomInt(100000, 1000000),
};
