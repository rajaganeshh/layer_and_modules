import api from "./axiosinstance";

export const authorizationUrl = (params) =>{
  return api.post("/authorizationurl",{
    params
  });
}

export const getToken = (keyName, value) => {
  return api.post(
    `/token`,
    { [keyName]: value } // Dynamically set the key name
  );
};

export const isuserloggedin = async (path) => {
  return api.get(`/isuserloggedin${path ? `?path=${path}` : "" }`);
};

export const Logout = async () => {
  return api.get(`/logout`);
};

export const GetAllIncidents = async () => {
  return api.get(`/getallincidents`);
};

export const GetIncident = async (incidentId) => {
  return api.get(`/getincident?incidentId=${incidentId}`);
};

export const UpdateWorkNotes = async (params) => {
  return api.post(`/updateworknotes`,{
    params
  });
};

export const RefreshWorkNotes = async (params) => {
  return api.post(`/refreshworknotes`,{
    params
  });
};

export const FeedBack = async (params) => {
  return api.post(`/feedback`,{
    params
  });
};

export const ChatAgent = async (params) => {
  return api.post(`/chatagent`,{
    params
  });
};
