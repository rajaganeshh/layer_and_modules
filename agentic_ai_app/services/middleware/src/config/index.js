const _ = require("lodash");
const glob = require("glob");

// eslint-disable-next-line n/no-unpublished-require
const config = _.merge(require("./env/routesconfig"));

module.exports = config;

module.exports.getPath = (globPatterns, excludes) => {
  const urlRegex = new RegExp("^(?:[a-z]+:)?//", "i"),
    self = this;
  let output = [];
  if (_.isArray(globPatterns))
    globPatterns.forEach((globPattern) => {
      output = _.union(output, self.getPath(globPattern, excludes));
    });
  else if (_.isString(globPatterns))
    if (urlRegex.test(globPatterns)) output.push(globPatterns);
    else {
      let files = glob.sync(globPatterns);
      if (excludes)
        files = files.map((file) => {
          let newFile = file;
          if (_.isArray(excludes))
            for (const i in excludes) newFile = file.replace(excludes[i], "");
          else newFile = file.replace(excludes, "");
          return newFile;
        });
      output = _.union(output, files);
    }
  return output;
};
