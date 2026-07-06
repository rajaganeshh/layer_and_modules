const { Sequelize, DataTypes } = require("sequelize");
const sequelize = require("../connection/dbconnection");
const sessionDetails = sequelize.define(
  "session",
  {
    id: {
      type: Sequelize.UUID,
      defaultValue: Sequelize.UUIDV4,
      allowNull: false,
      primaryKey: true,
    },
    accessToken: {
      type: DataTypes.TEXT,
    },
    refreshToken: {
      type: DataTypes.TEXT,
    },
    userid: {
      type: DataTypes.TEXT,
    },
    expiry: {
      type: DataTypes.DATE,
    },
  },
  { timestamps: true, schema: JSON.parse(process.env.secrets).database.schema }
);

module.exports = { sessionDetails };
