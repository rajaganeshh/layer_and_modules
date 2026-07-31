const {
  SecretsManagerClient,
  GetSecretValueCommand,
} = require("@aws-sdk/client-secrets-manager");
const fs = require("fs");
const path = require("path");
const { check } = require("zod");
const client = new SecretsManagerClient({
  region: process.env.region,
});

async function getSecret(secretName) {
  try {
    const command = new GetSecretValueCommand({ SecretId: secretName });
    const response = await client.send(command);
    if (response.SecretString) {
      return JSON.parse(response.SecretString);
    }
    // if stored as binary
    const buff = Buffer.from(response.SecretString);
    return buff.toString("ascii");
  } catch (error) {
    throw error;
  }
}
module.exports.check = async () => {
  try {
    const secretName =process.env.secret_name
    console.log("----------started getting the secrets-----------");
    let secret = await getSecret(secretName);
    secret = await JSON.parse(secret["nodeSecrets"]);
    process.env.secrets = JSON.stringify(secret)
    return secret;
  } catch (error) {
    throw error;
  }
};
