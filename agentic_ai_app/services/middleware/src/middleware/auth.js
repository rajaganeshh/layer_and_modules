const { error } = require("winston");
const routes = require("../config/env/routes.json");
const { getSession } = require("../sharedfunction/session");
const { profile } = require("../utilites/profile");
const { AppError } = require("./exception");

/**
 * it's a user authorization middleware
 * @param {*} req path
 * @param {*} res autorize or not
 * @param {*} next
 */
module.exports.auth = async (req, res, next) => {
  try {
    const { path } = req;
    const endPointName = path.substring(path.lastIndexOf("/") + 1);
    if (routes["No-Authentication"].includes(endPointName)) return next();
    const { session: authorization } = req.cookies;
    //check session cookie is there or not
    if (!authorization) throw new AppError("Session Expired, Redirecting to login page", { status: 401 });
    const session = await getSession(authorization);
    if (!session)
      throw new AppError("Session Expired, Redirecting to login page", {
        status: 401,
      });
    //need to authenticate the user request
    const userDetails = await profile(session.accessToken).catch((error) => {
      throw error;
    });
    req.locals = { userDetails };
    next();
  } catch (error) {
    error.status ??= 401;
    next(error);
  }
};
