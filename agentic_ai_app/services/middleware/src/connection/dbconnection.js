const { Sequelize } = require("sequelize");

const sequelize = new Sequelize(
  JSON.parse(process.env.secrets).database.database,
  JSON.parse(process.env.secrets).database.user,
  JSON.parse(process.env.secrets).database.password,
  {
    host: JSON.parse(process.env.secrets).database.host,
    dialect: "postgres",
    //added this options because while connecting to db from code from ECS environmen it got resolved with the below thing
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false,
      },
    },
    port: JSON.parse(process.env.secrets).database.port,
  }
);

// require("../authenticate/login/model/user");
sequelize.authenticate();
sequelize
  .createSchema(JSON.parse(process.env.secrets).database.schema, { ifNotExists: true })
  .catch((error) => {
    if (error.original.code == "42P06") console.log("schema already exist.");
  });
sequelize.sync(); //this create the table, if it's not there along with schema
module.exports = sequelize;
