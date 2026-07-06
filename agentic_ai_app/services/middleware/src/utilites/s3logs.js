const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");
const path = require("path");
const fs = require("fs");

const s3 = new S3Client({
  endpoint: JSON.parse(process.env.secrets).s3.endpoint,
  region: process.env.region,
  forcePathStyle: true,
});

module.exports.logsToSS3 = async (req, res, next) => {
  try {
    const logdir = path.join(__dirname, "..", "logs");
    if (!fs.existsSync(logdir)) {
      console.log("-----log folder is not there-----");
    }
    const files = fs.readdirSync(logdir);
    for (const file of files) {
      const filepath = path.join(logdir, file);
      if (fs.lstatSync(filepath).isDirectory()) continue;
      const fileContent = fs.readFileSync(filepath, "utf8");
      const command = new PutObjectCommand({
        Bucket: JSON.parse(process.env.secrets).s3.bucket,
        Key: `${JSON.parse(process.env.secrets).s3.prefix}/${file}`,
        Body: fileContent,
        ContentType: "text/plain",
      });
      await s3.send(command);
      console.log(`uploaded ${file} to s3`);
    }
  } catch (error) {
    //  don't let the server crashed
    try {
      const { log } = require("./logs");
      if (typeof log === "function") {
        log().error("----error while uploading the logs------", {
          from: "logs to ss3",
          functionName: "logsToSS3",
          error,
        });
      }
    } catch (_loggerError) {
      // ignore logger failures during best-effort S3 upload
    }
    console.log("----error while uploading the logs------");
  }
};
