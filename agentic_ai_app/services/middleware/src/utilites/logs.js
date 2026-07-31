const { format, createLogger, Logger} = require("winston");
const DailyRotateFile = require("winston-daily-rotate-file");
const { randomNumber } = require("../config/app/constant");
const WinstonCloudwatch = require("winston-cloudwatch");

const { combine, timestamp, printf } = format;
const logFormatter = ({
  timestamp,
  tenant,
  level,
  from,
  functionName,
  message,
  error,
  ...args
}) => {
  const logData = {
    timestamp,
    tenant,
    level,
    from,
    functionName,
    logMessage: message,
    ...args,
  };
  if (level === "error" && error !== undefined) {
    logData["error"] = error;
    logData["errorMessage"] = error?.message;
    logData["errorName"] = error?.name;
    logData["errorCode"] = error?.code;
    logData["errorStack"] = error?.stack;
    logData["errorCause"] = error?.cause;
    logData["status"] = error?.status;
    logData["errorString"] = error.toString();
    logData["stringifiedError"] = JSON.stringify(error);
  }

  // this is for passing the logs to cloudwatch
  const logger= createLogger({
     transports: [
    new WinstonCloudwatch({
      logGroupName: JSON.parse(process.env.secrets).s3.logGroupName,
      logStreamName: JSON.parse(process.env.secrets).s3.logStreamName,
      awsRegion: process.env.region,
      jsonMessage: true,
    })
  ]
  })
logger.info(logData);
  return JSON.stringify(logData);
};

/**
 * Logger
 *
 * @param {string} [organizationName=application] - Organization Name. Default
 *   is `application`
 * @returns {Logger} Winston Logger
 */
const logger = (organizationName = "application") => {
  const options = {
    defaultMeta: { tenant: organizationName },
    transports: [
      new DailyRotateFile({
        filename: `logs/${organizationName}_%DATE%_${randomNumber}.log`,
        datePattern: "DD_MM_YYYY",
        level: "debug",
        format: combine(
          timestamp({ format: "YYYY-MM-DD HH:mm:ss:SSS" }),
          printf(logFormatter)
        ),
      }),
    ],
  };

  return createLogger(options);
};

const loggers = {};

/**
 * Writes logs to a log file '<loggerName_<DD_MM_YYYY>_<randomNumber>.log'
 *
 * @param {string} [loggerName=application] - Log File Name (Database
 *   Container). Default is `application`
 * @returns {Logger} Winston Logger
 */
const log = (loggerName = "application") => {
  if (loggers[loggerName]) return loggers[loggerName];
  const newLogger = logger(loggerName);
  loggers[loggerName] = newLogger;
  return newLogger;
};

module.exports = { log };
