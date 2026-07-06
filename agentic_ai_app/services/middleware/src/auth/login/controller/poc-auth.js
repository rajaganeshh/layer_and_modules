const isValidCookieDomain = (domain) => {
  if (!domain || typeof domain !== "string") {
    return false;
  }

  const trimmed = domain.trim();
  if (!trimmed || trimmed.toLowerCase() === "localhost") {
    return false;
  }

  // RFC-friendly hostname pattern for cookie Domain attribute.
  return /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/.test(trimmed);
};

const buildCookieOptions = (maxAge) => {
  const secrets = JSON.parse(process.env.secrets || "{}");
  const cookie = secrets.cookie || {};
  const options = {
    maxAge,
    secure: cookie.secure,
    httpOnly: cookie.httpOnly,
    sameSite: cookie.sameSite,
    path: cookie.path || "/",
  };

  if (isValidCookieDomain(cookie.domain)) {
    options.domain = cookie.domain.trim();
  }

  return options;
};

const POC_USER_ID = "vaadmin";
const POC_DISPLAY_NAME = "vaadmin";

const getLoginRedirectUrl = (req) => {
  const requestOrigin = req.get("origin");
  if (requestOrigin && requestOrigin !== "*") {
    return `${requestOrigin.replace(/\/$/, "")}/login`;
  }

  const secrets = JSON.parse(process.env.secrets || "{}");
  const origin = secrets.app?.origin;

  if (Array.isArray(origin) && origin.length > 0) {
    const firstOrigin = origin[0];
    if (firstOrigin && firstOrigin !== "*") {
      return `${firstOrigin.replace(/\/$/, "")}/login`;
    }
  }

  if (typeof origin === "string" && origin.trim() && origin !== "*") {
    return `${origin.replace(/\/$/, "")}/login`;
  }

  return "http://localhost:3000/login";
};

module.exports.authorizationUrlController = async (req, res, next) => {
  try {
    const username = String(req.body?.params?.username || "").trim().toLowerCase();
    if (username !== POC_USER_ID) {
      return res.status(403).send({ message: "Only POC user vaadmin is allowed" });
    }

    const redirectUrl = getLoginRedirectUrl(req);
    const code = `poc-${POC_USER_ID}`;

    res.status(200).send({
      message: `${redirectUrl}?code=${encodeURIComponent(code)}`,
    });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

module.exports.tokenController = async (req, res, next) => {
  try {
    const code = req.body?.code;
    if (!code) {
      return res.status(400).send({ message: "code is required" });
    }

    const normalizedCode = String(code).trim().toLowerCase();
    if (normalizedCode !== `poc-${POC_USER_ID}`) {
      return res.status(403).send({ message: "Invalid POC auth code" });
    }

    const userId = POC_USER_ID;
    const displayName = POC_DISPLAY_NAME;

    const sessionValue = Buffer.from(`${userId}:${Date.now()}`).toString("base64url");

    res.cookie("session", sessionValue, buildCookieOptions(3600 * 1000));
    res.cookie("refreshToken", sessionValue, buildCookieOptions(3600 * 1000));

    res.status(200).send({
      message: {
        id: userId,
        displayName,
        jobTitle: "Demo User",
      },
    });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

module.exports.isUserLoggedInController = async (req, res, next) => {
  try {
    const path = req.query?.path;
    if (path) {
      res.cookie("redirecturl", path, buildCookieOptions(undefined));
    }

    const session = req.cookies?.session;
    if (!session) {
      return res.status(200).send({
        condition: false,
        jobTitle: null,
        userId: null,
        displayName: null,
      });
    }

    return res.status(200).send({
      condition: true,
      jobTitle: "Demo User",
      userId: POC_USER_ID,
      displayName: POC_DISPLAY_NAME,
    });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

module.exports.logoutController = async (req, res, next) => {
  try {
    const clearOptions = buildCookieOptions(0);

    res.clearCookie("redirecturl", clearOptions);
    res.clearCookie("session", clearOptions);
    res.clearCookie("refreshToken", clearOptions);

    res.status(200).send({ message: "Logged out successfully" });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

module.exports.health = (_req, res) => {
  res.status(200).send({ message: "Middleware is up" });
};
