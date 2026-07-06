const {
  getAllIncidentController,
  getIncidentController,
  updateWorknotesController,
  feedbackHandler,
  refreshWorknotesHandler,
  chatAgentHandler,
} = require("../controller/incidents");

module.exports = (app) => {
  app.get("/getallincidents", getAllIncidentController);
  app.get("/getincident", getIncidentController);
  app.post("/updateworknotes",updateWorknotesController)
  app.post("/feedback", feedbackHandler)
  app.post("/refreshworknotes",refreshWorknotesHandler)
  app.post("/chatagent",chatAgentHandler)
};
