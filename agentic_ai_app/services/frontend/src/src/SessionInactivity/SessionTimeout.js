import { useEffect } from 'react';

import { useNavigate } from "react-router-dom";
import { toast } from 'react-toastify';
import { Logout } from '../services/ApiCalls';

import { useGlobalContext } from '../Global/GlobalContext';

function SessionTimeout({ timeout }) {
    const {
      
      
     
      } = useGlobalContext()
    let navigate = useNavigate();
  useEffect(() => {
    let timeoutId;

    const resetTimeout = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(logout, timeout);
    };

    const logout = () => {
      navigate("/login");
      // Logout()
      //         .then((response) => {
      //           window.location.href = response.data.message;
      
      //           navigate("/login");
      //         })
      //         .catch((error) => {
      //           toast.error(error.response.data.message);
              
      //         });
    
    };

    const onActivity = () => {
      resetTimeout();
    };

    // Attach event listeners to monitor user activity
    document.addEventListener('mousemove', onActivity);
    document.addEventListener('keydown', onActivity);

    // Start the timeout
    resetTimeout();

    // Clean up event listeners when the component unmounts
    return () => {
      document.removeEventListener('mousemove', onActivity);
      document.removeEventListener('keydown', onActivity);
      clearTimeout(timeoutId);
    };
  }, [timeout]);

  return null;
}

export default SessionTimeout;