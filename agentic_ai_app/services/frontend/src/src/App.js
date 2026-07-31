import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LoginPage from "./screens/loginpage"
import Dashboard from "./screens/dashboard"
import { GlobalProvider } from "./Global/GlobalContext";
import AgenticAIScreen from "./screens/AgenticAIScreen";
import { ToastContainer } from "react-toastify";
import HomePage from "./screens/HomePage";
import { Navigate } from "react-router-dom";
import { lazy } from "react";

import Loader from "./components/Loader";
import SessionTimeout from "./SessionInactivity/SessionTimeout";

const LazyDasboard = lazy(() => import ("./screens/dashboard"))
const LazyAgenticScreen = lazy(() => import ("./screens/AgenticAIScreen"))


const App = () => {
  return (
    <GlobalProvider>
      <Router>
        <SessionTimeout timeout={3600000}/>
          <Loader /> 
        <Routes>
          {/* Route for Login Page */}
           <Route path="/" element={<Navigate to="/login" />} />
          <Route path="/login" element={<LoginPage />} />

          {/* AppLayout with Dashboard as the default route */}
          <Route path="/easyjet" element={<HomePage />}>
            <Route index element={<Navigate to="/easyjet/MIM-Agents-Platform" />} /> {/* Redirect to Dashboard */}
            <Route path="/easyjet/MIM-Agents-Platform" element={<LazyDasboard />} />
            

          </Route>
          <Route path="/AgenticAI/:ticketId" element={<LazyAgenticScreen />} />
        </Routes>
      </Router>
      <ToastContainer />
    </GlobalProvider>
  );
};

export default App;
