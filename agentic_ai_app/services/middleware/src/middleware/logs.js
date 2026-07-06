const { log } = require("../utilites/logs");
const { logsToSS3 } = require("../utilites/s3logs");

module.exports.logger = (req, res, next) => {
  try {
    const startTime = performance.now();
    let responseBody;
    const resDotSend = res.send;
    res.send = (data) => {
      responseBody = typeof data == "object" ? JSON.stringify(data) : data;
      res.send = resDotSend;
      return res.send(data);
    };
    res.on("finish", () => {
      const endTime = performance.now();
      if (res.statusCode >= 200 && res.statusCode < 400) {
        log("middleware_logs").info("Api success", {
          from: "Logger middleware",
          functionName: "logger",
          path: req.originalUrl,
          userId: req.locals?.userDetails.id,
          status: res.statusCode,
          role: req.locals?.userDetails.jobTitle,
          timeElapsed: `${Math.round(endTime - startTime)} ms`,
        });
      } else {
        log("middleware_logs").error("API failed.", {
          from: "logger middleware",
          functionName: "logger",
          path: req.originalUrl,
          userId: req.locals?.userDetails.id,
          role: req.locals?.userDetails.jobTitle,
          error: { error:responseBody, status: res.statusCode },
          timeElapsed: `${Math.round(endTime - startTime)} ms`,
        });
      }
      logsToSS3();
    });
    next();
  } catch (error) {}
};
