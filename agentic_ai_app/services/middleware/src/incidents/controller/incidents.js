const { log } = require("../../utilites/logs");
const { pythonApi } = require("../../utilites/pythonapi");



module.exports.chatAgentHandler =async (req,res,next)=>{
  try {
    const {inc_id, mode, user_message}= req.body.params
    const details={
      method:"post",
      payload:{
        incId:inc_id,
        mode:!mode?"":mode,
        user_message
      },
      endpoint:JSON.parse(process.env.secrets).pythonApi.chatBot
    }
    const response = await pythonApi(details)
    res.status(200).send({message:response.message})
  } catch (error) {
    error.status??=400
    next(error)
  }
}

/**
 * this is for  telling python to update the worknotes
 * @param {* incident number} req 
 * @param {*} res 
 * @param {*} next 
 */
module.exports.refreshWorknotesHandler =async (req,res,next)=>{
  try {
    const{incident_number}= req.body.params
    const details ={
      method:"post",
      url:`${JSON.parse(process.env.secrets).app.interface_url}`,
      payload:{incident_number},
      endpoint:JSON.parse(process.env.secrets).pythonApi.refreshWorkNote
    }
    const response = await pythonApi(details)
    res.status(200).send({message:response.message})
  } catch (error) {
    error.status??=400
    next(error)
  }
}


/**
 * this is for feedback handler
 * @param {* feedbackMode, comments, incidentId} req 
 * @param {*} res 
 * @param {*} next 
 */
module.exports.feedbackHandler =(req,res,next)=>{
  try {
    const{feedbackMode, comments,incidentId}= req.body.params
    // const startTime = performance.now();
    // const endTime = performance.now();
    log("feedback_logs").info(`feedback given`,{
      from:"logging the feedback",
      functionName:"feedbackHandler",
      path:req.originalUrl,
      incidentId,
      feedbackMode,
      comments,
      userId: req.locals?.userDetails.id,
      role: req.locals?.userDetails.jobTitle,
      // timeElapsed: `${Math.round(endTime - startTime)} ms`
    })
    res.status(200).send({message:"feedback noted successfully."})
  } catch (error) {
    error.status??=400
    next(error)
  }
}

/**
 * this is for updating the worknotes in servicenow
 * @param {* incident_number,user_name,work_note} req 
 * @param {*} res 
 * @param {*} next 
 */
module.exports.updateWorknotesController =async (req,res,next)=>{
  try {
    const {incident_number,user_name,work_note} = req.body.params
    const details={
      method:'post',
      payload:{incident_number,
      user_name,
      work_note,},
      url:`${JSON.parse(process.env.secrets).app.interface_url}`,
      endpoint:JSON.parse(process.env.secrets).pythonApi.updateWorknote
    }
    await pythonApi(details)
    res.status(200).send({message:'successfully update the worknotes'})
  } catch (error) {
    error.status??=400
    next(error)
  }
}

/**
 * this is for getting a particular incident details
 * @param {* incidentId} req 
 * @param {* details of incident} res 
 * @param {*} next 
 */

module.exports.getIncidentController = async (req, res, next) => {
  try {
    const { incidentId } = req.query;
    const data = {
      method: "get",
      endpoint: `${JSON.parse(process.env.secrets).pythonApi.getIncident}?incId=${encodeURIComponent(
        incidentId
      )}`,
    };
    const response = await pythonApi(data);
    const { worknotes } = response.message
    if(worknotes){
    const entries = worknotes.split(/\n\n+/)
    const result =[]
    if(entries.length!=0){
      for(let i=0;i<entries.length;i++){
      let ans ="";
      const entry = entries[i];
      if(!entry?.trim()) continue;
      const match = entry.match(/^(?:=)?(\d{1,2}[ -]\d{1,2}[ -]\d{2,4}\s+\d{1,2}:\d{1,2}:\d{1,2})(?:\s+-\s+|\s+)(.*?)\s+\(Work notes\)(?:\s*\r?\n|\s*)(.+?)$/s);
      if (match) {
      let [, timestamp, username, message] = match;
      // Skip if it's a system entry
      if (username?.trim() === "System") continue;
      // Add parsed data to result array
      if(username?.trim()==="agent api user"){
        username = message?.trim().split('-')[0]
        message =message?.trim().split('-')[1]
      }
      ans+=timestamp?.trim()+" "+username?.trim()+" "+message?.trim()
      result.push(ans);
    }
    }
    }
    response.message['worknotes']=result
    }
    res.status(200).send({ message: response.message });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};

/**
 * this is for getting the all incidents
 * @param {*} req
 * @param {*} res
 * @param {*} next
 */
module.exports.getAllIncidentController = async (req, res, next) => {
  try {
    const data = {
      method: "get",
      endpoint: JSON.parse(process.env.secrets).pythonApi.getAllIncident,
    };
    const incidents = await pythonApi(data);
    res.status(200).send({ message: incidents.message });
  } catch (error) {
    error.status ??= 400;
    next(error);
  }
};
