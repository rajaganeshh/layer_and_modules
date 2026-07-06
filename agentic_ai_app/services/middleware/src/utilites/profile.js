const { AppError } = require("../middleware/exception");
const {
  loggedInUserDetails,
  isUserInGroup,
} = require("../sharedfunction/user");

module.exports.profile = async (authorization) => {
  try {
    let user = await loggedInUserDetails(authorization);
    // need to check whether the user is onboarded in AD group or not
    await isUserInGroup({
      accessToken: authorization,
      userId: user.id,
    });
    return user;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};
