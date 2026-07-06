const { DateTime } = require("luxon");
const { sessionDetails } = require("../dbschema/session");

module.exports.getSessionWithUserId = async (userId) => {
  try {
    const session = await sessionDetails.findAll({
      where: { userid: userId },
      raw: true,
    });
    return session;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};
/**
 * for getting the session based on sessionID
 * @param {*} sessionId
 * @returns
 */
module.exports.getSession = async (sessionId) => {
  try {
    const session = await sessionDetails.findOne({
      where: { id: sessionId },
      raw: true,
    });
    return session;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};

/**
 * for deleting the session on the basis of sessionid
 * @param {*} sessionId
 */
module.exports.deleteSession = async (sessionId) => {
  try {
    await sessionDetails.destroy({ where: { id: sessionId } });
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};

/**
 * for creating a session of loggedin user
 * @param {*access_token,refresh_token} token
 * @param {*login user objectId} userId
 * @returns
 */

module.exports.createSession = async (token, userId) => {
  try {
    const expiresIn = DateTime.now()
      .plus({ seconds: token.expires_in })
      .toUTC()
      .toISO();
    await sessionDetails.sync({ alter: true });
    const item = await sessionDetails.create({
      accessToken: token.access_token,
      refreshToken: token.refresh_token,
      userid: userId,
      expiry: expiresIn,
      raw: true,
    });
    return item;
  } catch (error) {
    error.status ??= 400;
    throw error;
  }
};
