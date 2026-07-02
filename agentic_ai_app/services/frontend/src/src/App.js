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
import { CssBaseline, ThemeProvider } from "@mui/material";
import virginTheme from "./theme/virginTheme";

import Loader from "./components/Loader";

const LazyDasboard = lazy(() => import ("./screens/dashboard"))
const LazyAgenticScreen = lazy(() => import ("./screens/AgenticAIScreen"))


const App = () => {
  return (
    <ThemeProvider theme={virginTheme}>
      <CssBaseline />
      <GlobalProvider>
        <Router>
            <Loader /> 
          <Routes>
            {/* Route for Login Page */}
             <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/login" element={<LoginPage />} />

            {/* AppLayout with Dashboard as the default route */}
            <Route path="/vaa" element={<HomePage />}>
              <Route index element={<Navigate to="/vaa/MIM-Agents-Platform" />} /> {/* Redirect to Dashboard */}
              <Route path="/vaa/MIM-Agents-Platform" element={<LazyDasboard />} />
            

            </Route>
            <Route path="/AgenticAI/:ticketId" element={<LazyAgenticScreen />} />
          </Routes>
        </Router>
        <ToastContainer />
      </GlobalProvider>
    </ThemeProvider>
  );
};

export default App;

