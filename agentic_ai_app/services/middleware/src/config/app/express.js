const express = require("express");
const bodyparser = require("body-parser");
const cookieParser = require("cookie-parser");
const https = require("node:https");
const { errorhandling } = require("../../middleware/errorhandling");
const path = require("node:path");
const cors = require("cors");
const app = express();
const config = require("../index");
const compression = require("compression");
const { doubleCsrf } = require("csrf-csrf");
const { setCsrfSecretCredentials } = require("../../sharedfunction/csrf-token");
const { apiPrefix } = require("../env/routesconfig");
const { readFileSync } = require("node:fs");
const { auth } = require("../../middleware/auth");
const { logger } = require("../../middleware/logs");
const http = require("http");
const { getsercrets } = require("../../utilites/getsecrets");
const { logsToSS3 } = require("../../utilites/s3logs");

const { generateToken, doubleCsrfProtection } = doubleCsrf({
  getSecret: () => setCsrfSecretCredentials(),
  cookieName: JSON.parse(process.env.secrets).cookie.csrfCookieName,
  cookieOptions: {
    domain: JSON.parse(process.env.secrets).cookie.domain,
    httpOnly: JSON.parse(process.env.secrets).cookie.httpOnly,
    secure: JSON.parse(process.env.secrets).cookie.secure,
    sameSite: JSON.parse(process.env.secrets).cookie.sameSite,
    path: "/",
  },
  size: 64,
  getTokenFromRequest: (req) => req.headers[JSON.parse(process.env.secrets).cookie.csrfCookie],
});

module.exports.initMiddleware = () => {
  app.use(cookieParser());
  app.use(compression());
  app.use(bodyparser.json({ limit: "50mb" }));
  app.use(express.json({ limit: "50mb" }));
  // app.use(bodyparser.urlencoded({ extended: false }));
  app.disable("x-powered-by");
  app.use((req, res, next) => {
    res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST");
    const csrfToken = generateToken(req, res, true);
    res.cookie(JSON.parse(process.env.secrets).cookie.csrfCookie, csrfToken, {
      domain: JSON.parse(process.env.secrets).cookie.domain,
      secure: JSON.parse(process.env.secrets).cookie.secure,
      sameSite: JSON.parse(process.env.secrets).cookie.sameSite,
      path: "/",
    });
    if (!JSON.parse(process.env.secrets).allowedMethods.includes(req.method)) {
      return res.status(400).send("Method not allowed");
    }
    next();
  });
  app.use(doubleCsrfProtection);
};

/**
 *  this is for all the auth routes in easyjet
 * @returns routers
 */
module.exports.auth = () => {
  const router = express.Router();
  config.getPath("./auth/!(base)/routes/*.js").forEach((route) => {
    require(path.resolve(route))(router);
  });
  return router;
};

/**
 * this is for all the incidents routes in easyjet
 * @returns
 */
module.exports.incident = () => {
  const router = express.Router();
  config.getPath("./incidents/routes/*.js").forEach((route) => {
    require(path.resolve(route))(router);
  });
  return router;
};
module.exports.initRoutes = (app) => {
  const authenticate = this.auth();
  const incidentRoutes = this.incident();
  app.use(
    apiPrefix,
    [
      cors({
        origin: JSON.parse(process.env.secrets).app.origin,
      }),
      logger,
    ],
    auth,
    authenticate
  );
  app.use(
    apiPrefix,
    [
      cors({
        origin: JSON.parse(process.env.secrets).app.origin,
      }),
      logger,
    ],
    auth,
    incidentRoutes
  );
};

module.exports.createserver = async () => {
  const httpsServer = http.createServer(app);
  return httpsServer;
};
module.exports.errorHandling = () => app.use(errorhandling);

module.exports.init = () => {
  this.initMiddleware();
  this.initRoutes(app);
  this.errorHandling();
  return this.createserver();
};
