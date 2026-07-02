import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

const PrivateRoute = ({ isUserLoggedIn, setRedirectPath }) => {
  const location = useLocation();

  if (!isUserLoggedIn) {
    // Store the current location in state
    if(location.pathname === "/"){
        setRedirectPath("")
    }
    else{
 setRedirectPath(location.pathname); 
    }
   
    return <Navigate to="/login" />;
  }

  // If the user is logged in, render the child routes
  return <Outlet />;
};

export default PrivateRoute;
