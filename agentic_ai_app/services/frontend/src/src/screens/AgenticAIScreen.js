import React, { useContext, useEffect, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Collapse,
  Stack,
  Avatar,
  List,
  ListItem,
  Tooltip,
  ListItemText,
  TextField,
  InputAdornment,
  TablePagination,
  Menu,MenuItem
} from "@mui/material";
import {
  KeyboardArrowLeft,
  KeyboardArrowRight,
  Storage,
} from "@mui/icons-material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import SendIcon from "@mui/icons-material/Send";
import mimImage from "../assets/mim_Image.png";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import ChatAssistant from "../components/ChatAssistant"; // Import the ChatAssistant component
import { useGlobalContext } from "../Global/GlobalContext";
import { DataViewer, HolidayPopup } from "../components/DataViewer";

import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { FeedBack, GetIncident, isuserloggedin, Logout, RefreshWorkNotes, UpdateWorkNotes } from "../services/ApiCalls";
import LogoutIcon from "@mui/icons-material/Logout";
import ConfirmationDialog from "../components/ConfirmationDialog";


const AgenticAIScreen = () => {
  const navigate = useNavigate();
  const location = useLocation()
  const { ticketId } = useParams();
  const {
    selectedTicket,
    setSelectedTicket,
    showLoader,
    hideLoader,
    setUserDetails,
    userDetails
  } = useGlobalContext();
  const [expanded, setExpanded] = useState(true);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false); // State to manage chat assistant visibility
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogContent, setDialogContent] = useState({});
  const [dialogTitle, setDialogTitle] = useState("");
  const [holidayDialogOpen, setHolidayDialogOpen] = useState(false);
  const [holidayDialogContent, setHolidayDialogContent] = useState({});
  const [holidayDialogTitle, setHolidayDialogTitle] = useState("");
  const [disabledButton,setDisabledButton] = useState(null)
  const [comments,setComments] = useState("")
  const [knowledgeBaseExpanded, setKnowledgeBaseExpanded] = useState(false);
  const [suspectedChangesPage, setSuspectedChangesPage] = useState(0);
  const [suspectedIncidentsPage, setSuspectedIncidentsPage] = useState(0);
  const [similarIncidentsPage, setSimilarIncidentsPage] = useState(0);
  const [knowledgeBasePage, setKnowledgeBasePage] = useState(0);
   const [transcriptsPage, setTranscriptsPage] = useState(0);
   const [focusedField,setFocusedField] = useState("")

  const rowsPerPage = 3;
  const currentIncidentId =
    selectedTicket?.ticketDetails?.incidentId ||
    selectedTicket?.incidentId ||
    ticketId ||
    "NIL";

  const incidentCI = (
    selectedTicket?.ticketDetails?.configurationItem ||
    selectedTicket?.ticketDetails?.cmdb_ci ||
    selectedTicket?.ticketDetails?.cmdbCi ||
    selectedTicket?.configurationItem ||
    ""
  ).toLowerCase();

  // Normalize CI text so matching works across case, punctuation, and spacing variants.
  const normalizedIncidentCI = incidentCI
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const compactIncidentCI = normalizedIncidentCI.replace(/\s+/g, "");
  const isTravelboxCI =
    normalizedIncidentCI.includes("tbox") ||
    normalizedIncidentCI.includes("travelbox") ||
    compactIncidentCI.includes("tboxtravelbox");
  const isVaaWebsiteCI = compactIncidentCI.includes("vaawebsite");

  const ciTranscriptRows = isTravelboxCI
    ? [
        {
          source: "Teams-0234",
          incidentId: currentIncidentId,
          link: "https://example.com/Teams-0234",
          summary:
            "Speaker 1: Users reported that they were unable to log in to the TravelBox application and received authentication errors. Speaker 2: After reviewing application and identity provider logs, the team identified that the Azure AD client secret used for authentication had expired, causing login requests to fail. Speaker 3: A new client secret was generated, the application configuration was updated, and the services were redeployed successfully. Post-deployment validation confirmed that users could log in normally, and the TravelBox application was restored to full functionality. The team also recommended implementing secret expiry monitoring and renewal alerts to prevent similar issues in the future.",
        },
      ]
    : isVaaWebsiteCI
    ? [
        {
          source: "Teams-0345",
          incidentId: currentIncidentId,
          link: "https://example.com/Teams-0345",
          summary:
            "Speaker 1: Users reported that they were unable to complete ticket bookings in the VAA Website application, with transactions failing during the payment confirmation stage. Speaker 2: The support team analyzed application logs and identified that the booking service was unable to communicate with the payment gateway due to a temporary API connectivity issue. Speaker 3: The team restored the integration by updating the API endpoint configuration and restarting the affected services. After conducting end-to-end testing, ticket bookings were processed successfully, payments were confirmed, and confirmation notifications were delivered to users. The issue was resolved, and monitoring was enhanced to detect similar integration failures proactively.",
        },
      ]
    : selectedTicket?.transcripts || [];
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState(null);
    const handleProfileMenuOpen = (event) => {
      setAnchorEl(event.currentTarget);
    };
  
    const handleProfileMenuClose = () => {
      setAnchorEl(null);
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
                
  const handleDialogOpen = (title, content) => {
    setDialogTitle(title);
    setDialogContent(content);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleHolidayDialogClose = () => {
    setHolidayDialogOpen(false);
  };
  // Sample data for table (can be replaced with dynamic data if available)

  const [bulletPoints, setBulletPoints] = useState(selectedTicket?.worknotes);

  const [rootCausePoints, setRootCausePoints] = useState([
    "Issue with the batch job which ran last night, the job was re-run with freed memory space to fix this problem",
  ]);

  // State to store the input value
  const [inputValue, setInputValue] = useState("");
  const [suggestions, setSuggestions] = useState("");
  const [rootCause, setRootCause] = useState("");

  const handleAddBulletPoint = () => {
  showLoader()
  let params ={
   number: selectedTicket?.ticketDetails?.incidentId ? selectedTicket?.ticketDetails?.incidentId  : "",
   user_name: userDetails?.displayName ? userDetails?.displayName : "",
   work_note: inputValue ? inputValue : "",
    }
    // if (inputValue.trim() !== "") {
    //   // Append the new bullet point to the existing string
    //   const updatedBulletPoints = bulletPoints
    //     ? `${bulletPoints}\n${inputValue}` // Append to the existing string
    //     : inputValue; // If empty, just set the input value

    //   setBulletPoints(updatedBulletPoints); // Update the state
    //   setInputValue(""); // Clear the input field
    // }

    UpdateWorkNotes(params).then((response) => {
      toast(response.data.message)
      setInputValue(""); // Clear the input field
      // handleAgenticAI()
      let params = {
        number:selectedTicket.ticketDetails.incidentId,
      }
      RefreshWorkNotes(params).then((response) => {
        handleAgenticAI()
        // setBulletPoints(response.data.message)
        hideLoader()
      })
      .catch((error) => {
        toast.error(error.response.data.message)
        hideLoader()
      })

    })
    .catch((error) => {
      toast.error(error.response.data.message)
      hideLoader()
    })
  };

  const handleCommentSend = () => {
    let params = {
    incidentId : ticketId ? ticketId : "",
    comments : comments ? comments : "",
    feedbackMode : disabledButton ? disabledButton : "",
   }

   FeedBack(params).then((response) => {
    toast(response.data.message)
    setComments("")
    setDisabledButton("")
   })
   .catch((error) => {
    toast.error(error.response.data.message)
   })
  };

  const handleReviews = (reviewtype) => {
    setDisabledButton(reviewtype)
  };

  const handleAddRootCausePoint = () => {
    if (rootCause.trim() !== "") {
      setRootCausePoints([...rootCausePoints, rootCause]); // Add the new bullet point
      setRootCause(""); // Clear the input field
    }
  };

  const handleApiCalls = async () => {
    try {
      const response = await isuserloggedin(location.pathname);
    
      // Check if the response data is valid
      if (!response.data.condition) {
        navigate("/login");
        return; // Exit early if response data is invalid
      }

      // Check session status and role
      if (response.data.condition) {
        setUserDetails(response.data);
      }
    } catch (error) {
      toast(error.response.data.message);
    }
  };

  const handleAgenticAI = () => {
    showLoader();
    GetIncident(ticketId)
      .then((response) => {
        setSelectedTicket(response.data.message); // Store the ticket in global state
        setBulletPoints(response.data.message.worknotes)
        hideLoader();
      })
      .catch((error) => {
        toast.error(error.response.data.message);
        hideLoader();
      });
  };

  useEffect(() => {
    if (ticketId) {
      handleAgenticAI();
    }

    handleApiCalls();
  }, []);

  useEffect(() => {
    setTranscriptsPage(0);
  }, [ticketId, incidentCI]);

  const StatusDot = ({ color = "green" }) => (
    <Avatar
      sx={{
        bgcolor: color,
        width: 10,
        height: 10,
      }}
    />
  );

  const menuItems = [
    { label: "ServiceNow", status: "green" },
    { label: "Confluence", status: "green" },
    { label: "Share point", status: "red" },
    { label: "Teams", status: "red" },
  ];

const handleKeyDown = (e) => {
   if(e.key === "Enter"){
    if(focusedField === "worknotes"){
      handleAddBulletPoint()
    }
    else if(focusedField === "comments" && disabledButton){
      handleCommentSend()
    }
   }
}

const handleBack = () => {
  navigate("/vaa")
}

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        height: "100vh",
        backgroundColor: "white",
      }}
    >
      {/* Main Content */}
      <Box
        sx={{
          flex: isChatOpen ? 0.7 : 1, // Shrink when chat is open
          transition: "flex 0.3s ease", // Smooth transition
          overflow: "auto",
        }}
      >
        {/* AppBar */}
        <AppBar
          position="static"
          elevation={0}
          sx={{ backgroundColor: "white", height: "4rem" }}
        >
          <Toolbar
            sx={{
              display: "flex",
              justifyContent: "space-between",
              px: "10px !important",
            }}
          >
            {/* Left End: Datasources Section */}
            <Box sx= {{display:"flex",flexDirection:"row", gap:1}}>
             <IconButton
              onClick ={() => handleBack()}
              size="small"
                sx={{ ml: 1, color: "#B1125B" }}><KeyboardArrowLeft/></IconButton>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                border: "1px solid #ddd",
                borderRadius: 2,
                px: 2,
                gap:2,
                bgcolor: "#fff",
                boxShadow: 1,
                width: "fit-content",
              }}
            >
             
              {/* Always-visible "Data Sources" */}
              <Box sx={{ display: "flex", alignItems: "center", mr: 2 }}>
                <Storage fontSize="small" sx={{ mr: 1, color: "black" }} />
                <Typography
                  variant="body1"
                  fontWeight={500}
                  sx={{ color: "black" }}
                >
                  Data Sources
                </Typography>
              </Box>

              {/* Expandable Menu Items */}
              <Collapse orientation="horizontal" in={expanded}>
                <Stack direction="row" spacing={1} alignItems="center">
                  {menuItems.map((item, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        border: "2px solid lightgrey",
                        gap: 1,
                        px: 1,
                        borderRadius: "10px",
                      }}
                    >
                      <StatusDot
                        color={item.status === "green" ? "green" : "red"}
                      />
                      <Typography variant="body1" sx={{ color: "black" }}>
                        {item.label}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Collapse>

              {/* Toggle Button */}
              <IconButton
                onClick={() => setExpanded(!expanded)}
                size="small"
                sx={{ ml: 1, color: "black" }}
              >
                {expanded ? <KeyboardArrowLeft /> : <KeyboardArrowRight />}
              </IconButton>
            </Box>
            </Box>

            {/* Right End: Profile Icon */}
            <IconButton sx={{ color: "black" }} onClick={handleProfileMenuOpen}>
              <AccountCircleIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

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

        {/* Cards Section */}
        <Box
          sx={{
            display: "flex",
            padding: "20px 20px 100px 20px",
            flexDirection: "column",
          }}
        >
          <Box
            sx={{
              display: "flex",
              gap: 2,
              mb: 2,
              opacity:
                selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            {/* First Card */}

            <Card
              sx={{
                flex: 1,
                backgroundColor: "#FCE7F1",
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <CardContent>
                <Typography sx={{ fontWeight: "bold", fontSize: "20px" }}>
                  Ticket Details
                </Typography>
                <Box sx={{ marginTop: 1 }}>
                  <Typography variant="body2">
                    <strong>Incident ID:</strong>{" "}
                    {selectedTicket?.ticketDetails?.incidentId || "NIL"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Short Description:</strong>{" "}
                    {selectedTicket?.ticketDetails?.shortDescription || "NIL"}
                  </Typography>
                </Box>
              </CardContent>
            </Card>

            {/* Second Card */}
            <Card
              sx={{
                flex: 1,
                backgroundColor: "#FCE7F1",
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <CardContent>
                <Typography sx={{ fontWeight: "bold", fontSize: "20px" }}>
                  Description
                </Typography>
                <Box sx={{ marginTop: 1 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      whiteSpace: "pre-wrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      display: "-webkit-box",
                      WebkitLineClamp: descriptionExpanded ? "none" : 4,
                      WebkitBoxOrient: "vertical",
                    }}
                  >
                    {selectedTicket?.ticketDetails?.decription || "NIL"}
                  </Typography>
                  <Button
                    onClick={() => setDescriptionExpanded(!descriptionExpanded)}
                    sx={{ textTransform: "none", padding: 0, marginTop: 1 }}
                  >
                    {descriptionExpanded ? "Show Less" : "Show More"}
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {/* Third Card */}
            <Card
              sx={{
                flex: 1,
                backgroundColor: "#FCE7F1",
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <CardContent>
                <Typography sx={{ fontWeight: "bold", fontSize: "20px" }}>
                  Additional Details
                </Typography>
                <Box sx={{ marginTop: 1 }}>
                  <Typography variant="body2">
                    <strong>Category:</strong>{" "}
                    {selectedTicket?.ticketDetails?.category || "NIL"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Assigned to:</strong>{" "}
                    {selectedTicket?.ticketDetails?.assignedTo || "NIL"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Created:</strong>{" "}
                    {selectedTicket?.ticketDetails?.created || "NIL"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Created by:</strong>{" "}
                    {selectedTicket?.ticketDetails?.createdBy || "NIL"}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Urgency:</strong>{" "}
                    {selectedTicket?.ticketDetails?.urgency || "NIL"}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
            {!isChatOpen && 
             <Card
             onClick = {() => setIsChatOpen(true)}
              sx={{
                display:"contents",
                width:"200px",
                p : "0px !important",
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
                cursor:"pointer"
              }}
            >
              <CardContent
              sx={{
                  p : "0px !important",
              }}>
              <img
            src={mimImage}
            style={{
              width:"100%",
              height:"200px"
            }}
            
          />
                
              </CardContent>
            </Card>}
            
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              opacity:
                selectedTicket?.ticketDetails?.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails?.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            <Typography
              sx={{
                color: "#B1125B",
                fontWeight: "bold",
                fontSize: "20px",
              }}
            >
              Suspected Changes (Last 3 days)
            </Typography>

            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Change ID",
                      "Short Description",
                      "Assigned to",
                      "Planned Start Date",
                      "Planned End Date",
                      "Configuration Item",
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTicket?.suspectedChanges?.length > 0 ? (
                    selectedTicket?.suspectedChanges
                      .slice(
                        suspectedChangesPage * rowsPerPage,
                        suspectedChangesPage * rowsPerPage + rowsPerPage
                      )
                      .map((row, index) => (
                        <TableRow key={index}>
                          <TableCell><a href={row.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ textDecoration: "none", color: "blue" }}>{row.changeId} </a></TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.shortDescription || "NIL"}
                              </Typography>

                              {(row.description || row.shortDescription) && (
                                <Tooltip title="View Description">
                                  <IconButton
                                    onClick={(e) => {
                                      e.stopPropagation(); // Prevent row click from triggering
                                      handleDialogOpen("Information", {
                                        Description: row.description || "NIL",
                                        "Short Description":
                                          row.shortDescription || "NIL",
                                      });
                                    }}
                                  >
                                    <VisibilityIcon
                                      fontSize="small"
                                      style={{ color: "grey" }}
                                    />
                                  </IconButton>
                                </Tooltip>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{row.assignedTo || "NIL"}</TableCell>
                          <TableCell>{row.plannedStartDate || "NIL"}</TableCell>
                          <TableCell>{row.plannedEndDate || "NIL"}</TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                justifyContent:"space-between"
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.configurationItem || "NIL"}
                              </Typography>
                              {/* <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.summary || "NIL"}
                              </Typography> */}

                              <Tooltip title="View Information">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent row click from triggering
                                    handleDialogOpen("Information", {
                                      Summary: row.summary || "NIL",
                                      "Configuration Item":  row.configurationItem||"NIL",
                                      Backout: row.backout || "NIL",
                                      "Impacted Services": row.impactedServices || "NIL",
                                      Category: row.category || "NIL",
                                      State: row.state || "NIL",
                                      "Implementation Plan":
                                        row.implimentationPlan || "NIL",
                                      "Post Implementation":
                                        row.postImplementation || "NIL",
                                    });
                                  }}
                                >
                                  <InfoOutlinedIcon
                                    fontSize="small"
                                    style={{ color: "grey" }}
                                  />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Suspected Changes Found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={selectedTicket?.suspectedChanges?.length || 0}
              page={suspectedChangesPage}
              onPageChange={(event, newPage) =>
                setSuspectedChangesPage(newPage)
              }
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[rowsPerPage]}
            />
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              opacity:
                selectedTicket?.ticketDetails?.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails?.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            <Typography
              sx={{
                color: "#B1125B",
                fontWeight: "bold",
                fontSize: "20px",
              }}
            >
              Suspected Incidents (Last 3 days)
            </Typography>

            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Incident ID",
                      "Short Description",
                      "Priority",
                      "Assigned Group",
                      "Business Service",
                      "Configuration Item",
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTicket?.suspectedIncidents?.length > 0 ? (
                    selectedTicket?.suspectedIncidents
                      .slice(
                        suspectedIncidentsPage * rowsPerPage,
                        suspectedIncidentsPage * rowsPerPage + rowsPerPage
                      )
                      .map((row, index) => (
                        <TableRow key={index}>
                          <TableCell><a href={row.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ textDecoration: "none", color: "blue" }}>{row.incidentId} </a></TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.shortDescription || "NIL"}
                              </Typography>
                              {(row.description || row.shortDescription) && (
                                <Tooltip title="View Description">
                                  <IconButton
                                    onClick={(e) => {
                                      e.stopPropagation(); // Prevent row click from triggering
                                      handleDialogOpen("Information", {
                                        Description: row.description || "NIL",
                                        "Short Description":
                                          row.shortDescription || "NIL",
                                      });
                                    }}
                                  >
                                    <VisibilityIcon
                                      fontSize="small"
                                      style={{ color: "grey" }}
                                    />
                                  </IconButton>
                                </Tooltip>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{row.priority || "NIL"}</TableCell>
                          <TableCell>{row.assignedGroup || "NIL"}</TableCell>
                          <TableCell>{row.businessService || "NIL"}</TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                justifyContent:"space-between"
                              }}
                            >
                                 <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.configurationItem || "NIL"}
                              </Typography>
                              {/* <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.summary || "NIL"}
                              </Typography> */}
                              <Tooltip title="View Information">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent row click from triggering
                                    handleDialogOpen("Information", {
                                      Summary: row.summary || "NIL",
                                      "Configuration Item": row.configurationItem||"NIL",
                                      "Work Notes and Comments":
                                        row.workNotes || "NIL",
                                      Resolution: row.resolution || "NIL",
                                      "Impacted Services": row.impactedServices || "NIL",
                                      Category: row.category || "NIL",
                                    });
                                  }}
                                >
                                  <InfoOutlinedIcon
                                    fontSize="small"
                                    style={{ color: "grey" }}
                                  />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Suspected Incidents found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={selectedTicket?.suspectedIncidents?.length || 0}
              page={suspectedIncidentsPage}
              onPageChange={(event, newPage) =>
                setSuspectedIncidentsPage(newPage)
              }
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[rowsPerPage]}
            />
          </Box>

          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              mb: 2,
              opacity:
                selectedTicket?.ticketDetails?.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails?.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            <Typography
              sx={{
                color: "#B1125B",
                fontWeight: "bold",
                fontSize: "20px",
              }}
            >
              Similar Incidents (Last 12 months)
            </Typography>

            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Incident ID",
                      "Short Description",
                      "Priority",
                      "Assigned Group",
                      "Business Service",
                      "Configuration Item",
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTicket?.similarIncidents?.length > 0 ? (
                    selectedTicket?.similarIncidents
                      .slice(
                        similarIncidentsPage * rowsPerPage,
                        similarIncidentsPage * rowsPerPage + rowsPerPage
                      )
                      .map((row, index) => (
                        <TableRow key={index}>
                          <TableCell><a href={row.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ textDecoration: "none", color: "blue" }}>{row.incidentId} </a></TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.shortDescription || "NIL"}
                              </Typography>

                              {(row.description || row.shortDescription) && (
                                <Tooltip title="View Description">
                                  <IconButton
                                    onClick={(e) => {
                                      e.stopPropagation(); // Prevent row click from triggering
                                      handleDialogOpen("Information", {
                                        Description: row.description || "NIL",
                                        "Short Description":
                                          row.shortDescription || "NIL",
                                      });
                                    }}
                                  >
                                    <VisibilityIcon
                                      fontSize="small"
                                      style={{ color: "grey" }}
                                    />
                                  </IconButton>
                                </Tooltip>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{row.priority || "NIL"}</TableCell>
                          <TableCell>{row.assignedGroup || "NIL"}</TableCell>
                          <TableCell>{row.businessService || "NIL"}</TableCell>
                          <TableCell sx={{ maxWidth: "200px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                justifyContent:"space-between"
                              }}
                            >
                                 <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.configurationItem || "NIL"}
                              </Typography>
                              {/* <Typography
                                sx={{
                                  maxWidth: "400px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.summary || "NIL"}
                              </Typography> */}

                              <Tooltip title="View Information">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent row click from triggering
                                    handleDialogOpen("Information", {
                                      Summary: row.summary || "NIL",
                                      "Configuration Item": row.configurationItem||"NIL",
                                      "Work Notes and Comments":
                                        row.workNotes || "NIL",
                                      "Impacted Services": row.impactedServices || "NIL",
                                      Resolution: row.resolution || "NIL",
                                      Category: row.category || "NIL",
                                    });
                                  }}
                                >
                                  <InfoOutlinedIcon
                                    fontSize="small"
                                    style={{ color: "grey" }}
                                  />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Similar Incidents found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={selectedTicket?.similarIncidents?.length || 0}
              page={similarIncidentsPage}
              onPageChange={(event, newPage) =>
                setSimilarIncidentsPage(newPage)
              }
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[rowsPerPage]}
            />
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              mb: 2,
              opacity:
                selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            <Typography
              sx={{
                color: "#B1125B",
                fontWeight: "bold",
                fontSize: "20px",
              }}
            >
              Knowledge Base
            </Typography>

            {/*
            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Scenario (Incident Response Plan)",
                      "Incident Priority",
                      "Full outage/degradation/temp tolerate",
                      "Application Service",
                      "Impact on Integrations",
                      "MIM Actions",
                      "Information",
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTicket?.incidentResponse.length > 0 ? (
                    selectedTicket?.incidentResponse.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell sx={{width: "500px" }}>
                          <a href={row.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ textDecoration: "none", color: "blue" }}>{row.scenario || "NIL"} </a>
                        </TableCell>
                        <TableCell>{row.priority}</TableCell>
                        <TableCell sx={{ width: "300px" }}>
                          {row.outage || "NIL"}
                        </TableCell>
                        <TableCell>{row.applicationService || "NIL"}</TableCell>

                        <TableCell sx={{ width: "300px" }}>
                          {" "}
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Typography
                              sx={{
                                maxWidth: "300px", // Limit the width of the cell
                                whiteSpace: "nowrap",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                cursor: "pointer",
                              }}
                            >
                              {row.impact || "NIL"}
                            </Typography>

                            <Tooltip title="View Service Card Description">
                              <IconButton
                                onClick={() =>
                                  handleDialogOpen("Information", {
                                    "Impact on Provisioned Service": row.impact || "NIL",
                                  })
                                }
                              >
                                <VisibilityIcon
                                  fontSize="small"
                                  style={{ color: "grey" }}
                                />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ width: "300px" }}>
                          {" "}
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Typography
                              sx={{
                                maxWidth: "300px", // Limit the width of the cell
                                whiteSpace: "nowrap",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                cursor: "pointer",
                              }}
                            >
                              {row.MIMactions || "NIL"}
                            </Typography>

                            <Tooltip title="View Service Card Description">
                              <IconButton
                                onClick={() =>
                                  handleDialogOpen("Information", {
                                    "MIM Actions": row.MIMactions || "NIL",
                                  })
                                }
                              >
                                <VisibilityIcon
                                  fontSize="small"
                                  style={{ color: "grey" }}
                                />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="View Details">
                            <IconButton
                              onClick={(e) => {
                                e.stopPropagation(); // Prevent row click from triggering

                                handleDialogOpen(
                                  "Incident Response Plan Details",{
                                    "Scenario":row.scenario || "NIL",
                                    "Priority":row.priority || "NIL",
                                    "Outage":row.outage || "NIL",
                                    "Application Service":row.applicationService || "NIL",
                                    "Impact":row.impact || "NIL",
                                     "MIM Actions":row.MIMactions || "NIL",
                                    "Information":row.information || "NIL",
                                  }
                                  
                                );
                              }}
                            >
                              <InfoOutlinedIcon
                                fontSize="small"
                                style={{ color: "grey" }}
                              />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Incident Response Plans Found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            */}
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              mb: 2,
              opacity:
                selectedTicket?.ticketDetails?.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails?.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            {/* Table Section */}
            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Source",
                      "Knowledge ID",
                      "Summary",
                      "Comments",
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTicket?.knowledgebase?.length > 0 ? (
                    selectedTicket?.knowledgebase
                      .slice(
                        knowledgeBasePage * rowsPerPage,
                        knowledgeBasePage * rowsPerPage + rowsPerPage
                      )
                      .map((row, index) => (
                        <TableRow key={index}>
                          <TableCell sx={{ width: "200px" }}>
                            {row.source || "NIL"}
                          </TableCell>
                          <TableCell sx={{ width: "300px" }}>
                            <a href={row.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ textDecoration: "none", color: "blue" }}>{row.knowledgeId||"NIL"} </a>
                            {/* {row.knowledgeId || "NIL"} */}
                          </TableCell>
                          <TableCell sx={{ width: "500px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                justifyContent: "space-between",
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "500px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.summary || "NIL"}
                              </Typography>

                              <Tooltip title="View Description">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent row click from triggering
                                    handleDialogOpen("Information", {
                                      Summary: row.summary || "NIL",
                                    });
                                  }}
                                >
                                  <VisibilityIcon
                                    fontSize="small"
                                    style={{ color: "grey" }}
                                  />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ width: "700px" }}>
                            {row.comments || "NIL"}
                          </TableCell>
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Knowledge Articles found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={selectedTicket?.knowledgebase?.length || 0}
              page={knowledgeBasePage}
              onPageChange={(event, newPage) => setKnowledgeBasePage(newPage)}
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[rowsPerPage]}
            />
          </Box>

          <Typography
            sx={{
              color: "#B1125B",
              fontWeight: "bold",
              fontSize: "20px",
              opacity:
                selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            Teams Transcript
          </Typography>

          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              mb: 2,
              opacity:
                selectedTicket?.ticketDetails?.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails?.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            {/* Table Section */}
            <TableContainer
              component={Paper}
              sx={{
                marginTop: 1,
                borderRadius: "10px",
                boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)",
              }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow>
                    {[
                      "Source",
                      "incident ID",
                      "Summary"
                    ].map((header) => (
                      <TableCell
                        key={header}
                        sx={{ color: "white", fontWeight: "bold" }}
                      >
                        {header}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ciTranscriptRows?.length > 0 ? (
                    ciTranscriptRows
                      .slice(
                        transcriptsPage * rowsPerPage,
                        transcriptsPage * rowsPerPage + rowsPerPage
                      )
                      .map((row, index) => (
                        <TableRow key={index}>
                          <TableCell sx={{ width: "200px" }}>
                            {row.source || "NIL"}
                          </TableCell>
                          <TableCell sx={{ width: "300px" }}>
                            {row.link ? (
                              <a href={row.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ textDecoration: "none", color: "blue" }}>{row.incidentId||"NIL"} </a>
                            ) : (
                              row.incidentId || "NIL"
                            )}
                          </TableCell>
                          <TableCell sx={{ width: "500px" }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                justifyContent: "space-between",
                              }}
                            >
                              <Typography
                                sx={{
                                  maxWidth: "500px",
                                  whiteSpace: "nowrap",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  cursor: "pointer",
                                }}
                              >
                                {row.summary || "NIL"}
                              </Typography>

                              <Tooltip title="View Description">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation(); // Prevent row click from triggering
                                    handleDialogOpen("Information", {
                                      Summary: row.summary || "NIL",
                                    });
                                  }}
                                >
                                  <VisibilityIcon
                                    fontSize="small"
                                    style={{ color: "grey" }}
                                  />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                         
                        </TableRow>
                      ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        align="center"
                        sx={{ padding: "16px", fontStyle: "italic" }}
                      >
                        No Team Transcript found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={ciTranscriptRows?.length || 0}
              page={transcriptsPage}
              onPageChange={(event, newPage) => setTranscriptsPage(newPage)}
              rowsPerPage={rowsPerPage}
              rowsPerPageOptions={[rowsPerPage]}
            />
          </Box>

          <Typography
            sx={{
              color: "#B1125B",
              fontWeight: "bold",
              fontSize: "20px",
              opacity:
                selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            Worknotes
          </Typography>

          {/* Bullet Points */}
          <Box
            sx={{
              border: "1px solid #B1125B",
              p: 2,
              borderRadius: "10px",
              mb: 2,
              marginTop: 1,
              opacity:
                selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
              pointerEvents:
                selectedTicket?.ticketDetails.state === "Closed"
                  ? "none"
                  : "auto",
            }}
          >
            <Box sx={{ height: "10rem", overflow: "auto" }}>
              <List sx={{ pt: "0px !important" }}>
                {bulletPoints ? (
                  bulletPoints.map((point, index) => (
<ListItem key={index} disablePadding>
<ListItemText primary={`• ${point}`} />
</ListItem>
                                ))
                ) : (
                  <ListItem>
                    <ListItemText primary="Please add Work Notes" />
                  </ListItem>
                )}
              </List>
            </Box>

            {/* Description Box with Send Icon */}
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
              }}
            >
              <TextField
                fullWidth
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
                variant="outlined"
                placeholder="Type your worknotes here"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onFocus={(e) => setFocusedField("worknotes")}
                onKeyDown={(e) => handleKeyDown(e)}
              />
              <IconButton
                onClick={handleAddBulletPoint}
                disabled = {!inputValue}
                sx={{ marginLeft: "10px", color: "#B1125B" }}
              >
                <SendIcon />
              </IconButton>
            </Box>
          </Box>
          {selectedTicket?.ticketDetails.state === "Closed" && (
            <>
              <Typography
                sx={{
                  color: "#B1125B",
                  fontWeight: "bold",
                  fontSize: "20px",
                }}
              >
                {" "}
                Actual Root Cause & Solutions{" "}
              </Typography>
              {/* Bullet Points */}
              <Box
                sx={{
                  border: "1px solid #B1125B",
                  p: 2,
                  borderRadius: "10px",
                  marginTop: 1,
                  mb: 2,
                }}
              >
                <Box sx={{ height: "10rem", overflow: "auto" }}>
                  <List sx={{ pt: "0px !important" }}>
                    {rootCausePoints.map((point, index) => (
                      <ListItem key={index} disablePadding>
                        <ListItemText primary={`• ${point}`} />
                      </ListItem>
                    ))}
                  </List>
                </Box>

                {/* Description Box with Send Icon */}
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  <TextField
                    fullWidth
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
                    variant="outlined"
                    placeholder="Type your Suggestions here"
                    value={rootCause}
                    onChange={(e) => setRootCause(e.target.value)}
                  />
                  <IconButton
                    onClick={handleAddRootCausePoint}
                    sx={{ marginLeft: "10px", color: "#B1125B" }}
                  >
                    <SendIcon />
                  </IconButton>
                </Box>
              </Box>{" "}
            </>
          )}
          <Box sx={{ display: "flex", flexDirection: "row", gap: 2 }}>
            {/* Left Column */}
            <Box sx={{ display: "flex", flexDirection: "column", flex: 1 }}>
              <Typography
                sx={{
                  color: "#B1125B",
                  fontWeight: "bold",
                  fontSize: "20px",
                  marginBottom: "2px",
                  opacity:
                    selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
                  pointerEvents:
                    selectedTicket?.ticketDetails.state === "Closed"
                      ? "none"
                      : "auto",
                }}
              >
                Feedback
              </Typography>

              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 2,
                }}
              >
                <Button
                  variant="contained"
                  sx={{ backgroundColor: "#B1125B", pointerEvents:disabledButton === "helpful" ? "none" : "auto", opacity : disabledButton === "helpful" ? 0.5 : 1 }}
                  onClick={() => handleReviews("helpful")}
                >
                  Reviewed and Helpful
                </Button>
                <Button
                  variant="contained"
                  sx={{ backgroundColor: "#B1125B", pointerEvents:disabledButton === "not-useful" ? "none" : "auto", opacity : disabledButton === "not-useful" ? 0.5 : 1  }}
                  onClick={() => handleReviews("not-useful")}
                >
                  Reviewed and not useful
                </Button>
              </Box>
            </Box>

            {/* Right Column */}
            <Box sx={{ display: "flex", flexDirection: "column", flex: 3 }}>
              <Typography
                sx={{
                  color: "#B1125B",
                  fontWeight: "bold",
                  fontSize: "20px",
                  opacity:
                    selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
                  pointerEvents:
                    selectedTicket?.ticketDetails.state === "Closed"
                      ? "none"
                      : "auto",
                }}
              >
                Comments
              </Typography>

              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <TextField
                  fullWidth
                  multiline
                  rows={2.5}
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
                  variant="outlined"
                  placeholder="Type your comments here and submit feedback"
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  onFocus={(e) => setFocusedField("comments")}
                onKeyDown={(e) => handleKeyDown(e)}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={handleCommentSend}
                          disabled = {!disabledButton || !comments}
                          sx={{ color: "#B1125B" }}
                        >
                          <SendIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Chat Assistant */}
      <ChatAssistant
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        selectedTicket={selectedTicket}
      />

      {/* Floating Button */}
      {/* {!isChatOpen && (
        <Box
          sx={{
            position: "fixed",
            bottom: 16,
            right: 16,
            display: "flex",
            alignItems: "center",
            gap: 1,

            padding: "8px 16px",
            zIndex: 1000,
            cursor: "pointer",
            opacity: selectedTicket?.ticketDetails.state === "Closed" ? 0.5 : 1,
            pointerEvents:
              selectedTicket?.ticketDetails.state === "Closed"
                ? "none"
                : "auto",
          }}
          onClick={() => setIsChatOpen(true)}
        >
          <img
            src={mimImage}
            style={{
              width: "50px",
              height: "60px",
            }}
          />
        </Box>
      )} */}

      <DataViewer
        open={dialogOpen}
        onClose={handleDialogClose}
        title={dialogTitle}
        content={dialogContent}
      />
      <HolidayPopup
        open={holidayDialogOpen}
        onClose={handleHolidayDialogClose}
        title={holidayDialogTitle}
        content={holidayDialogContent}
      />

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

export default AgenticAIScreen;

