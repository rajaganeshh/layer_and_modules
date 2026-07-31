import React, { createContext, useContext, useState } from "react";

// Create the context
const GlobalContext = createContext();

// Create the provider component
export const GlobalProvider = ({ children }) => {
  // State to store the selected ticket
  const [selectedTicket, setSelectedTicket] = useState(null);
   const [loading, setLoading] = useState(false);
    const [userDetails, setUserDetails] = useState(false);
      const [incidents, setIncidents] = useState([]);
      const[status, setStatus] = useState("")

  const showLoader = () => setLoading(true);
  const hideLoader = () => setLoading(false);

  return (
    <GlobalContext.Provider value={{ status, setStatus, selectedTicket, setSelectedTicket, showLoader, hideLoader,loading,userDetails, setUserDetails,incidents, setIncidents }}>
      {children}
    </GlobalContext.Provider>
  );
};

// Custom hook to use the TicketContext
export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error("useTicketContext must be used within a TicketProvider");
  }
  return context;
};