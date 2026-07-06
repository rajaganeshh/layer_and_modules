module.exports.errorhandling = (error, req, res, _next) => {
  return res
    .status(error.status || 400)
    .send({
      code: "ApplicationError",
      status: error.status,
      message: error.message ? error.message : error.error,
    })
    .end();
};
