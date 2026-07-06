const { check } = require("./configconnectivity");

// /**
//  * first load the secrets
//  */
check()
  .then(() => {
    //Process.env stores everything as a secret
    const server = require("./config/app/express");
    process.env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0";
    const portlistener = JSON.parse(process.env.secrets).port;
    server.init().then((app) => {
      app.listen(portlistener, (error) => {
        if (error) console.log("Server failed to start ->", error);
        else console.log(`Application Started in Port ${portlistener}.`);
      });
    });
  })
  .catch((error) => {
    console.error("error geting secrets", error);
  });
