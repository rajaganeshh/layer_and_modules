import React, { useState, useEffect, useContext,useRef } from "react";
import {
  Container,
  Grid,
  TextField,
  Button,
  Box,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
// Import the image from the assets folder
import backgroundImage from "../assets/login_background.jpg";
import { authorizationUrl, getToken, isuserloggedin } from "../services/ApiCalls";
import { useGlobalContext } from "../Global/GlobalContext";
import Cookies from "js-cookie"

// Reference-only demo login switch.
// Default behavior remains unchanged unless REACT_APP_DEMO_LOGIN is explicitly set to true.
const isDemoReferenceMode = process.env.REACT_APP_DEMO_LOGIN === "true";
const allowedDemoUser = "vaadmin";
let hasInitializedLoginCheck = false;

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [credentials, setCredentials] = useState({
    username: "",
  
  });
    const isMounted = useRef(false);

  const { showLoader, hideLoader,setUserDetails } = useGlobalContext();

  const navigate = useNavigate();
  

  const getCodeFromUrl = () => {
    const searchParams = new URLSearchParams(window.location.search);
    return searchParams.get("code");
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

     const handleApiCalls = async () => {
    if (isDemoReferenceMode) {
      return;
    }

    try {
      const response = await isuserloggedin();
  
  
      // Check if the response data is valid
      if (!response.data.condition) {
        hideLoader()
        return; // Exit early if response data is invalid
      }
  
      showLoader()
 
  
      // Check session status and role
      if (response.data.condition) {
         
          navigate("/vaa");
          hideLoader()
        }
      
    } catch (error) {
      toast(error.response.data.message)
      hideLoader()
    }
  };
 
  useEffect(() => {
    if (hasInitializedLoginCheck) {
      return;
    }

    // Prevent duplicate initial auth checks in dev strict mode.
    hasInitializedLoginCheck = true;
    handleApiCalls();
  }, []);

  const handleLogin = () => {
    const normalizedUser = credentials.username?.trim().toLowerCase();

    if (!normalizedUser) {
      toast.error("Enter the username")
      hideLoader()
      return;
    }

    if (normalizedUser !== allowedDemoUser) {
      toast.error("Invalid user")
      hideLoader()
      return;
    }

    showLoader();

    if (isDemoReferenceMode) {
      setUserDetails({
        displayName: credentials.username,
        jobTitle: "Demo User",
      });
      hideLoader()
      toast("Demo login successful")
      navigate("/vaa");
      return;
    }

    let params = {
      username: normalizedUser,
 
    }
    authorizationUrl(params).then((response) => {
    
          window.location.href = response.data.message;
           
      
      
        hideLoader()
      })

        .catch((error) => {
          toast(error.response.data)
          hideLoader()
             navigate("/vaa");
        })

    // Add your login logic here

  };

  useEffect(() => {
    if (isDemoReferenceMode) {
      return;
    }

    const code = getCodeFromUrl();
    if (code) {
      const encryptcode = code
      getToken("code", encryptcode)
        .then((response) => {
          if (response.status === 200) {
            let pathname = Cookies.get("redirecturl")
            hideLoader()
            if(pathname){
              navigate(pathname)
            }
            else{
              navigate("/vaa");
            }
         
            toast("Logged in Successfully", {
              autoClose: 2000, // Toast will disappear after 3 seconds
            });
            setUserDetails(response.data.message)





          }
        })
        .catch((error) => {
          toast(error.response.data.message)
           hideLoader()
        });
    };

  }, []);

  return (
    <Box
      sx={{
        height: "100vh",
        width: "100vw",
        backgroundImage: `url(${backgroundImage})`, // Use the imported image
        backgroundSize: "cover",
        backgroundPosition: "center",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Container maxWidth="md">
        <Grid
          container
          spacing={2}
          sx={{
            height: "100%",
            display: "flex",
            alignItems: "center",
          }}
        >
          {/* Left Side */}
          <Grid
            item
            xs={12}
            md={6}
            sx={{
              display: "flex",
              justifyContent: "flex-start", // Align to the left
              mt: { xs: 8, md: 12 }, // Move the login form slightly lower
            }}
          >
            <Box
              sx={{
                backgroundColor: "rgba(255, 255, 255, 0.8)", // Semi-transparent background
                borderRadius: 2,
                width: "100%", // Make the form take full width of the grid
                maxWidth: 400, // Optional: Limit the form width
              }}
            >
              {/* Username Field */}
              <TextField
                label="Email ID"
                name="username"
                value={credentials.username}
                onChange={handleChange}
                fullWidth
                margin="normal"
                sx={{
                  "& .MuiOutlinedInput-root": {
                    "&:hover fieldset": {
                      borderColor: "#D81B60", // Orange border on hover
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "#D81B60", // Orange border on focus
                    },
                  },
                  "& .MuiInputLabel-root": {
                    color: "rgba(0, 0, 0, 0.6)", // Default label color
                  },
                  "& .MuiInputLabel-root.Mui-focused": {
                    color: "#D81B60", // Orange label on focus
                  },
                }}
              />

              {/* Login Button */}
              <Button
                variant="contained"
                fullWidth
                onClick={handleLogin}
                sx={{
                  marginTop: 2,
                  backgroundColor: "#B1125B", // Orange button
                  "&:hover": {
                    backgroundColor: "#7A003C", // Darker orange on hover
                  },
                }}
              >
                Login
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default LoginPage;
