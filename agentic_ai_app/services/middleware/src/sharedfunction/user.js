const { ExternalAPIError } = require("../middleware/exception");
const { getsercrets } = require("../utilites/getsecrets");

module.exports.isUserInGroup = async (data) => {
  try {
    const options = {
      method: "GET",
      headers: {
        "Content-type": "application/json",
        Authorization: `Bearer ${data.accessToken}`,
      },
    };
    const url = `${JSON.parse(process.env.secrets).officeCredentials.apiendpoint}/v1.0/groups/${JSON.parse(process.env.secrets).officeCredentials.groupId}/members/${data.userId}/$ref`;
    const response = await fetch(url, options);
    const validation = await response.json();
    if (!response.ok) {
      throw new ExternalAPIError("user group validation", {
        cause: validation,
        status: response.status ?? 400,
      });
    }
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};

/**
 * this is for getting the logged in userdetails
 * @param {* access_token} authorization
 * @returns
 */
module.exports.loggedInUserDetails = async (authorization) => {
  try {
    const options = {
      method: "GET",
      headers: {
        "Content-type": "application/json",
        Authorization: `Bearer ${authorization}`,
      },
    };
    const profilePath = `${JSON.parse(process.env.secrets).officeCredentials.apiendpoint}${JSON.parse(process.env.secrets).officeCredentials.userProfile}`;
    const response = await fetch(profilePath, options);
    const user = await response.json();
    if (!response.ok) {
      throw new ExternalAPIError("Profile Api Failes", {
        cause: user,
        status: response.status ?? 400,
      });
    }
    return user;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};
