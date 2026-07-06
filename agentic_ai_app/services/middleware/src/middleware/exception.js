class ApplicationError extends Error {
  constructor(
    message,
    args = { logMessage: "Application error.", cause: undefined, status: 400 }
  ) {
    super(message);
    this.name = this.constructor.name;
    this.status = args.status;
    this.code = this.errorCodes(this.status);
    this.cause = args.cause ? `${JSON.stringify(args.cause)}` : undefined;
    this.log(args.logMessage);
  }

  log(data) {
    const { log } = require("../utilites/logs");
    log().error(data, {
      from: "Custom error class.",
      functionName: this.constructor.name,
      error: {
        name: this.constructor.name,
        message: this.message,
        status: this.status,
        code: this.code,
        cause: this.cause,
        stack: this.stack,
      },
    });
    return null;
  }

  errorCodes(status) {
    if (status === 400) return "Bad Request";
    else if (status === 401) return "Unauthorized";
    else if (status === 403) return "Forbidden";
    else if (status === 404) return "Not Found";
  }
}

class AppError extends ApplicationError {
  constructor(message, args = { status: 400 }) {
    super(message, {
      logMessage: "Application error.",
      cause: args.cause || undefined,
      status: args.status,
    });
    this.name = this.constructor.name;
    this.status = args.status;
    this.code = super.errorCodes(this.status);
    this.cause = args.cause ? `${JSON.stringify(args.cause)}` : undefined;
  }
}

class AuthenticationError extends ApplicationError {
  constructor(message, args = { cause: undefined, status: 401 }) {
    super(message, {
      logMessage: "Authentication failed.",
      cause: args.cause,
      status: args.status,
    });
    this.name = this.constructor.name;
    this.status = args.status;
    this.code = super.errorCodes(this.status);
    this.cause = args.cause ? `${JSON.stringify(args.cause)}` : undefined;
  }
}

class ExternalAPIError extends ApplicationError {
  constructor(message, args = { cause: undefined, status: 400 }) {
    super(message, {
      logMessage: "Api failed.",
      cause: args.cause,
      status: args.status,
    });
    this.name = this.constructor.name;
    this.status = args.status;
    this.code = super.errorCodes(this.status);
    this.cause = args.cause ? `${JSON.stringify(args.cause)}` : undefined;
  }
}

module.exports = { AppError, AuthenticationError, ExternalAPIError };
