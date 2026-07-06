const { default: fetch } = require("node-fetch");
const { accessToken, logoutURL } = require("../../../sharedfunction/login");
const { profile } = require("../../../utilites/profile");
const {
  createSession,
  deleteSession,
  getSession,
  getSessionWithUserId,
} = require("../../../sharedfunction/session");
const { getsercrets } = require("../../../utilites/getsecrets");
const { authorizationUrl } = require("../../../utilites/authorizationurl");
const { loggedInUserDetails } = require("../../../sharedfunction/user");
const serverBuiltTime = new Date();

module.exports.logoutController = async (req, res, next) => {
  try {
    await deleteSession(req.cookies.session);
    await res.clearCookie("redirecturl",{
      domain: JSON.parse(process.env.secrets).cookie.domain,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      samSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: "/",
    });
    await res.clearCookie("session", {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      maxAge: 0,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      httpOnly: JSON.parse(process.env.secrets).cookie.httpOnly,
      sameSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: JSON.parse(process.env.secrets).cookie.path,
    });
    await res.clearCookie("refreshToken", {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      maxAge: 0,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      httpOnly: JSON.parse(process.env.secrets).cookie.httpOnly,
      sameSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: JSON.parse(process.env.secrets).cookie.path,
    });
    res
      .status(200)
      .send({ message: logoutURL(JSON.parse(process.env.secrets).officeCredentials.redirecturi) });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

/**
 * just checking whether the server is running or not
 * @param {*} req
 * @param {*} res
 * @param {*} _next
 */

module.exports.health = (req, res, _next) => {
  res.status(200).send({
    message: `Successfully connected to server. Build - ${serverBuiltTime.toString()}`,
  });
};

/**
 * generating the autorization url
 * @param {*} req none
 * @param {*} res none
 * @param {*} next none
 */
module.exports.authorizationUrlController = async (req, res, next) => {
  const { username} = req.body.params;
  res.status(200).send({
    message: authorizationUrl({
      tenantId: JSON.parse(process.env.secrets).officeCredentials.tenantId,
      clientId: JSON.parse(process.env.secrets).officeCredentials.clientId,
      scopes: JSON.parse(process.env.secrets).officeCredentials.scopes,
      redirectUrl: JSON.parse(process.env.secrets).officeCredentials.redirecturi,
      emailId: username,
    }),
  });
};

/**
 * for generating the access and refresh token
 * @param {*} req body or params will have a code
 * @param {*} res pass the user details of the loggedin user
 * @param {*} next
 */
module.exports.tokenController = async (req, res, next) => {
  try {
    //generate the accessToken and refreshtoken
    const token = await accessToken(
      req.body.code,
      JSON.parse(process.env.secrets).officeCredentials.redirecturi,
      {
        tenantId: JSON.parse(process.env.secrets).officeCredentials.tenantId,
        clientId: JSON.parse(process.env.secrets).officeCredentials.clientId,
        clientSecret: JSON.parse(process.env.secrets).officeCredentials.clientSecret,
        scopes: JSON.parse(process.env.secrets).officeCredentials.scopes,
      }
    );
    // get the userdetails of logged in user and check whether the user is onboarded into db or not
    const user = await profile(token.access_token);
    // create the session of the logged in user
    const session = await createSession(token, user.id);
    // set the cookies in browser
    await res.cookie("session", session.id, {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      maxAge: token.expires_in * JSON.parse(process.env.secrets).cookie.accessTokenLife,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      httpOnly: JSON.parse(process.env.secrets).cookie.httpOnly,
      samSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: JSON.parse(process.env.secrets).cookie.path,
    });
    await res.cookie("refreshToken", session.id, {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      maxAge: token.expires_in * JSON.parse(process.env.secrets).cookie.refreshTokenLife,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      httpOnly: JSON.parse(process.env.secrets).cookie.httpOnly,
      samSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: JSON.parse(process.env.secrets).cookie.path,
    });
    res.status(200).send({ message: user });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

/**
 * This is for checking if the session is active or not
 * @param {* cookies} req
 * @param {* boolean} res
 * @param {*} next
 * @returns
 */
module.exports.isUserLoggedInController = async (req, res, next) => {
  try {
    const { session } = req.cookies;
    const {path} =req.query
    if(path){
          await res.cookie("redirecturl", path, {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      samSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: "/",
    });
    }
    if (session === undefined)
      return res.status(200).send({
        jobTitle: null,
        userId: null,
        condition: false,
        displayName: null,
      });
    //to check whether the session is still active
    const sessionDetails = await getSession(session);
    let user;
    user = await loggedInUserDetails(sessionDetails.accessToken);
    return res.status(200).send({
      condition: true,
      jobTitle: user.jobTitle,
      userId: user.id,
      displayName: user.displayName,
    });
  } catch (error) {
    error.status = 400;
    error.error ??= "unauthorized";
    next(error);
  }
};
