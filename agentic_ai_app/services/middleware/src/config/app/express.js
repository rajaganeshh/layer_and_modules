const express = require("express");
const bodyparser = require("body-parser");
const cookieParser = require("cookie-parser");
const { errorhandling } = require("../../middleware/errorhandling");
const path = require("node:path");
const cors = require("cors");
const app = express();
const config = require("../index");
const compression = require("compression");
const { apiPrefix } = require("../env/routesconfig");
const { logger } = require("../../middleware/logs");
const http = require("http");

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
    if (!JSON.parse(process.env.secrets).allowedMethods.includes(req.method)) {
      return res.status(400).send("Method not allowed");
    }
    next();
  });
};

/**
 * this is for all POC auth routes
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
 * this is for all incident routes in middleware
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
  const authRoutes = this.auth();
  const incidentRoutes = this.incident();

  app.use(
    apiPrefix,
    [
      cors({
        origin: JSON.parse(process.env.secrets).app.origin,
      }),
      logger,
    ],
    authRoutes
  );

  app.use(
    apiPrefix,
    [
      cors({
        origin: JSON.parse(process.env.secrets).app.origin,
      }),
      logger,
    ],
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
