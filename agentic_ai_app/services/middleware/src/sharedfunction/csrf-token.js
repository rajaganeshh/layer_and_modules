
const { getsercrets } = require("../utilites/getsecrets");
const { log } = require("../utilites/logs");

module.exports.setCsrfSecretCredentials = async () => {
  try {
    const csrfSecret = JSON.parse(process.env.secrets).csrfTokenSecret;
    return csrfSecret;
  } catch (error) {
    log().error(`Setting 'csrfSecret' global variable failed.`, {
      from: "Keyvault",
      functionName: "setCsrfSecretCredentials",
      error,
    });
  }
};
