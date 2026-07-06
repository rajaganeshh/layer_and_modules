
const { getsercrets } = require("./getsecrets");

module.exports.authorizationUrl = (appConfig) => {
  const { tenantId, clientId, scopes, redirectUrl, emailId } = appConfig;
  return `${JSON.parse(process.env.secrets).officeCredentials.endpoint}${tenantId}${
    JSON.parse(process.env.secrets).officeCredentials.authorizePath
  }?client_id=${clientId}&response_type=code&redirect_uri=${redirectUrl}&response_mode=query&scope=${scopes.join(
    " "
  )}&state=12345&login_hint=${emailId}`;
};
