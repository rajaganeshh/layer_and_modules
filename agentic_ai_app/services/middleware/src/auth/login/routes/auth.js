const controller = require("../controller/auth");

module.exports = (app) => {
  app.post("/authorizationurl", controller.authorizationUrlController);
  app.post("/token", controller.tokenController);
  app.get("/isuserloggedin", controller.isUserLoggedInController);
  app.get("/health", controller.health);
  app.get("/logout", controller.logoutController);
};
