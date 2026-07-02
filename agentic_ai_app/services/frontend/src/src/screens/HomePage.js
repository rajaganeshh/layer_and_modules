import React, { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  IconButton,
  AppBar,
  Toolbar,
  useMediaQuery,
  Typography,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ConfirmationNumberIcon from "@mui/icons-material/ConfirmationNumber";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/Logout";
import companyLogo from "../assets/virginatlantic.png";
import ConfirmationDialog from "../components/ConfirmationDialog";
import NotificationsNoneIcon from "@mui/icons-material/NotificationsNone";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import StarIcon from "@mui/icons-material/Star";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { Logout } from "../services/ApiCalls";
import { toast } from "react-toastify";
import { useGlobalContext } from "../Global/GlobalContext";

const drawerWidth = 240;

const HomePage = () => {
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation(); // Get the current location
  const [anchorEl, setAnchorEl] = useState(null);

  const [isFavorite, setIsFavorite] = useState(false);
  const { showLoader, hideLoader, userDetails } = useGlobalContext();
  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleFavorite = () => {
    setIsFavorite((prev) => !prev);
  };

  const handleLogoutClick = () => {
    setLogoutDialogOpen(true); // Open the confirmation dialog
  };

  const handleLogoutConfirm = (confirmed) => {
    setLogoutDialogOpen(false); // Close the dialog
    if (confirmed) {
      showLoader();
      Logout()
        .then((response) => {
          window.location.href = response.data.message;

          navigate("/login");
        })
        .catch((error) => {
          toast.error(error.response.data.message);
          hideLoader();
        });
    }
  };

  // Use useMediaQuery to check screen size
  const isMobile = useMediaQuery("(max-width:960px)"); // Matches screens smaller than 960px

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen); // Toggle the drawer open/close state
  };

  const handleNavigation = (path) => {
    if (location.pathname !== path) {
      navigate(path);
    }
  };

  const drawerContent = (
    <Box
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        background: "linear-gradient(45deg, #7A003C, #B1125B)", // Improved orange gradient
        color: "#FFFFFF", // White text color
      }}
    >
      {/* Top Section */}
      <Box>
        <Box sx={{ display: "flex", width: "100%", justifyContent: "center" }}>
          <img
            src={companyLogo}
            alt="Company Logo"
            style={{ height: "90px", width: "80%", objectFit: "cover" }}
          />
        </Box>
        <List sx={{ padding: "0px !important" }}>
          {/* Major Incident Platform Menu */}
          <ListItem
            onClick={() => handleNavigation("/vaa/MIM-Agents-Platform")}
            sx={{
              cursor:
                location.pathname === "/vaa/MIM-Agents-Platform"
                  ? "default"
                  : "pointer",
              backgroundColor:
                location.pathname === "/vaa/MIM-Agents-Platform"
                  ? "#B1125B"
                  : "transparent", // Highlight the menu
              "&:hover": {
                backgroundColor:
                  location.pathname === "/vaa/MIM-Agents-Platform"
                    ? "#B1125B"
                    : "#7A003C", // Prevent hover effect if active
              },
            }}
            disabled={location.pathname === "/vaa/MIM-Agents-Platform"} // Disable if active
          >
            <ListItemIcon sx={{ color: "#FFFFFF" }}>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="MIM Agents Platform" />
          </ListItem>


        </List>
      </Box>

      {/* Bottom Section */}
      {isMobile &&
      <>
       <Box sx={{ display: "flex", justifyContent:"center", gap: 2 }}>
                <Tooltip title="Help">
                  <IconButton color="inherit">
                    <HelpOutlineIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Notifications">
                  <IconButton color="inherit">
                    <NotificationsNoneIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Profile">
                  <IconButton color="inherit" onClick={handleProfileMenuOpen}>
                    <AccountCircleIcon />
                  </IconButton>
                </Tooltip>
              </Box>
               <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
            >
              <MenuItem>
                <Typography variant="body2">
                  <b>Name:</b> {userDetails?.displayName}
                </Typography>
              </MenuItem>
              <MenuItem>
                <Typography variant="body2">
                  <b>Role:</b> {userDetails?.jobTitle}
                </Typography>
              </MenuItem>
              <MenuItem
                onClick={() => {
                  handleProfileMenuClose();
                  handleLogoutClick();
                }}
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <LogoutIcon />
                <Typography variant="body2">Logout</Typography>
              </MenuItem>
            </Menu></>}
        
    </Box>
  );

  return (
    <Box sx={{ display: "flex" }}>
      {/* AppBar for Mobile Screens */}

      {isMobile ? (
        <AppBar
          position="fixed"
          sx={{
            background: "linear-gradient(45deg, #7A003C, #B1125B)",
            height: "4rem",
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Box sx={{ flexGrow: 1 }}>
              <img
                src={companyLogo}
                alt="Company Logo"
                style={{ height: "90px", width: "120px", objectFit: "contain" }}
              />
            </Box>
          </Toolbar>
        </AppBar>
      ) : (
        // Permanent Drawer for Larger Screens
        <>
          {/* Permanent Drawer */}
          <Drawer
            variant="permanent"
            sx={{
              width: drawerWidth,
              flexShrink: 0,
              "& .MuiDrawer-paper": {
                width: drawerWidth,
                boxSizing: "border-box",
              },
            }}
          >
            {drawerContent}
          </Drawer>

          {/* AppBar */}
          <AppBar
            position="fixed"
            sx={{
              background: "black",
              height: "3rem",
              display: "flex",
              width: `calc(100% - ${drawerWidth}px)`, // Dynamically calculate the width
              marginLeft: `${drawerWidth}px`, // Offset the AppBar to the right of the Drawer
            }}
          >
            <Toolbar
              sx={{
                display: "flex",
                justifyContent: "space-between",
                minHeight: "48px !important",
              }}
            >
              {/* Center Section with Outline */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  flex: 1,

                  justifyContent: "center",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "row",
                    alignSelf: "center",
                    alignItems: "center",
                    border: "1px solid white",
                    borderRadius: "50px",
                    padding: "6px 20px",
                  }}
                >
                  <Typography
                    variant="body1"
                    sx={{ color: "white", marginRight: "8px" }}
                  >
                    Virgin Atlantic - MIM Dashboard
                  </Typography>
                  <IconButton
                    color="inherit"
                    onClick={toggleFavorite}
                    sx={{ p: "0px" }}
                  >
                    {isFavorite ? (
                      <StarIcon sx={{ color: "yellow" }} />
                    ) : (
                      <StarBorderIcon sx={{ color: "yellow" }} />
                    )}
                  </IconButton>
                </Box>
              </Box>

              {/* Right Section */}
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Tooltip title="Help">
                  <IconButton color="inherit">
                    <HelpOutlineIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Notifications">
                  <IconButton color="inherit">
                    <NotificationsNoneIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Profile">
                  <IconButton color="inherit" onClick={handleProfileMenuOpen}>
                    <AccountCircleIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Toolbar>

            {/* Profile Menu */}
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleProfileMenuClose}
              anchorOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
              transformOrigin={{
                vertical: "top",
                horizontal: "right",
              }}
            >
              <MenuItem>
                <Typography variant="body2">
                  <b>Name:</b> {userDetails?.displayName}
                </Typography>
              </MenuItem>
              <MenuItem>
                <Typography variant="body2">
                  <b>Role:</b> {userDetails?.jobTitle}
                </Typography>
              </MenuItem>
              <MenuItem
                onClick={() => {
                  handleProfileMenuClose();
                  handleLogoutClick();
                }}
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <LogoutIcon />
                <Typography variant="body2">Logout</Typography>
              </MenuItem>
            </Menu>
          </AppBar>
        </>
      )}

      {/* Temporary Drawer for Mobile Screens */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better performance on mobile
          }}
          sx={{
            "& .MuiDrawer-paper": {
              width: drawerWidth,
              boxSizing: "border-box",
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flex: 1,
          marginTop: isMobile ? "64px" : "44px", // Adjust for AppBar height on mobile
        }}
      >
        <Outlet />
      </Box>
      <ConfirmationDialog
        open={logoutDialogOpen}
        title="Confirm Logout"
        message="Are you sure you want to logout?"
        onConfirm={() => handleLogoutConfirm(true)}
        onCancel={() => handleLogoutConfirm(false)}
      />
    </Box>
  );
};

export default HomePage;

