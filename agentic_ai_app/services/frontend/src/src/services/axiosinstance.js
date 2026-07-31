import axios from 'axios';
import Cookies from 'js-cookie';
import { useNavigate } from 'react-router-dom';
 
 
const api = axios.create({
  baseURL: process.env.REACT_APP_NODE_API_BASE_URL,
  headers: {
    'Content-Type': `application/json`,
  },
  withCredentials: true,
});
 
api.interceptors.request.use(
  (config) => {
    const csrfToken = Cookies.get('x-csrf-token');
 
    if (csrfToken) {
      config.headers['x-csrf-token'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
 
// 🌀 Response Interceptor — Redirect to login on 401
api.interceptors.response.use(
  (response) => {
    // If the response is successful, return it as is
    return response;
  },
  (error) => {
    // Ensure error.response exists
    if (error.response) {
      const originalRequest = error.config;
     
      // Check if the error is a 401 Unauthorized
      if (error.response.status === 401) {
        // Prevent infinite redirect loops (e.g., if the login page itself triggers a 401)
        if (window.location.pathname !== '/login') {
          window.location.href = "/login"
        }
        return Promise.reject(error); // Reject the promise without retrying
      }
    }
 
    // Reject other errors as usual
    return Promise.reject(error);
  }
);
 
export default api;
 