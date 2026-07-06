module.exports.getsercrets = (path, fallback) => {
  try {
    if (!process.env["secrets"]) {
      return fallback; // no secrets at all
    }
    const parsed = JSON.parse(process.env["secrets"]);
    // if path is a string, convert to array
    const keys = Array.isArray(path) ? path : [path];
    const value = keys.reduce((obj, key) => obj?.[key], parsed);
    return value ?? fallback;
  } catch (error) {
    return fallback;
  }
};
