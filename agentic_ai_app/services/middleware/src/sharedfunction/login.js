
const { AuthenticationError } = require("../middleware/exception");
const { getsercrets } = require("../utilites/getsecrets");

/**
 * this is for generating the logouturl
 * @param {*} redirectUrl
 * @returns
 */
module.exports.logoutURL = (redirectUrl) => {
  return `${JSON.parse(process.env.secrets).officeCredentials.endpoint}${JSON.parse(process.env.secrets).officeCredentials.tenantId}/oauth2/logout?post_logout_redirect_uri=${redirectUrl}`;
};

/**
 * function for generating the access token
 * @param {* AD Code} code
 * @param {*} redirectUrl
 * @param {*} appConfig
 * @returns
 */
module.exports.accessToken = async (code, redirectUrl, appConfig) => {
  try {
    const { clientId, clientSecret, tenantId, scopes } = appConfig;
    const tokenParams = {
      /* eslint-disable camelcase*/
      code,
      redirect_uri: redirectUrl,
      scope: `${scopes.join(" ")}`,
      grant_type: "authorization_code",
      client_id: clientId,
      client_secret: clientSecret,
      /* eslint-enable camelcase */
    };
    
    const path = `${JSON.parse(process.env.secrets).officeCredentials.endpoint}${tenantId}${JSON.parse(process.env.secrets).officeCredentials.tokenPath}`;
    const requestBody = [];
    for (const params in tokenParams) {
      const encodedKey = encodeURIComponent(params);
      const encodedValue = encodeURIComponent(tokenParams[params]);
      requestBody.push(encodedKey + "=" + encodedValue);
    }
    const options = {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: requestBody.join("&"),
    };
    const response = await fetch(path, options);
    const token = await response.json();
    if (!response.ok) {
      
      throw new AuthenticationError("Access Token Failes", {
        cause: token,
        status: 403,
      });
    }
    return token;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};
