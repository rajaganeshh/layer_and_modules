const {
  SecretsManagerClient,
  GetSecretValueCommand,
} = require("@aws-sdk/client-secrets-manager");
const client = new SecretsManagerClient({
  region: process.env.region,
});

const defaultSecrets = {
  port: 3001,
  allowedMethods: ["GET", "POST", "OPTIONS"],
  app: {
    origin: "*",
    interface_url: "http://localhost:8000",
  },
  s3: {
    endpoint: "http://localhost:9000",
    bucket: "middleware-logs",
    prefix: "logs",
  },
  pythonApi: {},
};

const mergeWithDefaults = (inputSecrets) => {
  const incoming = inputSecrets || {};
  return {
    ...defaultSecrets,
    ...incoming,
    app: {
      ...defaultSecrets.app,
      ...(incoming.app || {}),
    },
    s3: {
      ...defaultSecrets.s3,
      ...(incoming.s3 || {}),
    },
    pythonApi: {
      ...defaultSecrets.pythonApi,
      ...(incoming.pythonApi || {}),
    },
  };
};

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
    if (process.env.secrets) {
      const parsedLocalSecrets = JSON.parse(process.env.secrets);
      const localSecrets = mergeWithDefaults(parsedLocalSecrets);
      process.env.secrets = JSON.stringify(localSecrets);
      return localSecrets;
    }

    const secretName = process.env.secret_name;
    if (!secretName) {
      process.env.secrets = JSON.stringify(defaultSecrets);
      return defaultSecrets;
    }

    console.log("----------started getting the secrets-----------");
    let secret = await getSecret(secretName);
    secret = await JSON.parse(secret["nodeSecrets"]);
    const mergedSecrets = mergeWithDefaults(secret);
    process.env.secrets = JSON.stringify(mergedSecrets);
    return mergedSecrets;
  } catch (error) {
    process.env.secrets = JSON.stringify(defaultSecrets);
    return defaultSecrets;
  }
};
