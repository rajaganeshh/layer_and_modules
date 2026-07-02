import axios from 'axios';
import Cookies from 'js-cookie';
 

const api = axios.create({
  baseURL: process.env.REACT_APP_NODE_API_BASE_URL,
  headers:{
    'Content-Type': `application/json`
  },
  withCredentials: true
});
 
// 🛡️ Request Interceptor — Add CSRF token to headers dynamically
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
 
// 🌀 Token refresh logic (unchanged from your code)
let isRefreshing = false;
let failedQueue = [];
 
const processQueue = (error = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};
 
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
 
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => api(originalRequest))
          .catch((err) => Promise.reject(err));
      }
 
      originalRequest._retry = true;
      isRefreshing = true;
 
      try {
        await axios.get(`${process.env.REACT_APP_NODE_API_BASE_URL}/refreshToken`, {
          withCredentials: true
        });
 
        processQueue();
        return api(originalRequest);
      } catch (err) {
        processQueue(err);
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
 
    return Promise.reject(error);
  }
);
 
export default api;
