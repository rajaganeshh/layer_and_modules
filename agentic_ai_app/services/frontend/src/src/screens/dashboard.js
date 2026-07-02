import React, { useEffect, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Box,
  TextField,
  InputAdornment,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  TableSortLabel,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

import { useLocation, useNavigate } from "react-router-dom";
import ClearIcon from "@mui/icons-material/Clear";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import ArrowBackIosIcon from "@mui/icons-material/ArrowBackIos";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import VisibilityIcon from "@mui/icons-material/Visibility";

import { DataViewer } from "../components/DataViewer";
import { useGlobalContext } from "../Global/GlobalContext";
import {
  GetAllIncidents,
  GetIncident,
  isuserloggedin,
} from "../services/ApiCalls";
import { toast } from "react-toastify";
import RefreshIcon from "@mui/icons-material/Refresh";
import { es } from "date-fns/locale/es";
import { format } from "date-fns";

const calculateOpenSince = (createdDate) => {
  // Convert the created date string to a Date object
  const created = new Date(createdDate);

  // Get the current date and time (you can replace this with `new Date()` for the actual current date)
  const now = new Date("2025-07-22"); // Example current date for testing

  // Calculate the difference in milliseconds
  const diffMs = now - created;

  // If the difference is negative, it means the created date is in the future
  if (diffMs < 0) {
    return "Created date is in the future";
  }

  // Calculate days, hours, and minutes
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffMs / (1000 * 60 * 60)) % 24);
  const minutes = Math.floor((diffMs / (1000 * 60)) % 60);

  // Format the result
  if (days > 0) {
    return `${days} day${days > 1 ? "s" : ""} ago`;
  } else if (hours > 0) {
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  } else {
    return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  }
};


const getStatusColor = (status) => {
  switch (status) {
    case "New":
      return "red";
    case "In Progress":
      return "#B1125B";
    case "Resolved":
      return "green";
    case "Closed":
      return "gray";
    default:
      return "black";
  }
};

const Dashboard = () => {
  const {
    setSelectedTicket,
    setIncidents,
    incidents,
    showLoader,
    hideLoader,
    setUserDetails,
  } = useGlobalContext();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 5;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogContent, setDialogContent] = useState({});
  const [dialogTitle, setDialogTitle] = useState("");

  const handleApiCalls = async () => {
    try {
      const response = await isuserloggedin(location.pathname);

      // Check if the response data is valid
      if (!response.data.condition) {
        hideLoader();
        navigate("/login");
        return; // Exit early if response data is invalid
      }

      showLoader();

      // Check session status and role
      if (response.data.condition) {
        hideLoader();
        setUserDetails(response.data);
      }
    } catch (error) {
      toast(error.response.data.message);
      hideLoader();
    }
  };

  useEffect(() => {
    handleApiCalls();
    showLoader();
    GetAllIncidents()
      .then((response) => {
        setIncidents(response.data.message);
        hideLoader();
      })
      .catch((error) => {
        toast.error(error.response.data.message);
        hideLoader();
      });
  }, []);


  const handleDialogOpen = (title, content) => {
    setDialogTitle(title);
    setDialogContent(content);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setCurrentPage(1); // Reset to the first page when changing tabs
  };

  const handleCardClick = (status) => {
    const tabIndex = [
      "All",
      "New",
      "In Progress",
      "Resolved",
      "Closed",
    ].indexOf(status);
    setTabValue(tabIndex);
    setCurrentPage(1); // Reset to the first page when changing tabs
  };

  const handleClearDates = () => {
    setFromDate(null);
    setToDate(null);
  };

  const today = new Date()
  const formattedTodayDate = format(today,"dd-MM-yyyy")

  // Filter tickets based on tab, search query, and date range
  // const filteredTickets = incidents.filter((ticket) => {
  //   // Convert the "Created" date to a Date object
  //   const createdDate = new Date(ticket.createdOn);

  //   // Check tabValue filters
  //   if (tabValue === 1 && ticket.state !== "New") return false;
  //   if (tabValue === 2 && ticket.state !== "In Progress") return false;
  //   if (tabValue === 3 && ticket.state !== "Resolved") return false;
  //   if (tabValue === 4 && ticket.state !== "Closed") return false;

  //   // Check search query filter
  //   if (searchQuery && !ticket.incidentId.includes(searchQuery)) return false;

  //   // Check date filters
  //   if (fromDate && createdDate <= new Date(fromDate)) return false; // Compare "Created" with "From Date"
  //   if (toDate && createdDate >= new Date(toDate)) return false; // Compare "Created" with "To Date"

  //   return true; // If all conditions pass, include the ticket
  // });
  const filteredTickets = incidents.filter((ticket) => {
  // Convert the "Created" date to a Date object
  const createdDate = new Date(ticket.createdOn);
 
  // Normalize the dates to ignore the time portion
  const normalizedCreatedDate = new Date(
    createdDate.getFullYear(),
    createdDate.getMonth(),
    createdDate.getDate()
  );
  const normalizedFromDate = fromDate
    ? new Date(fromDate.getFullYear(), fromDate.getMonth(), fromDate.getDate())
    : null;
  const normalizedToDate = toDate
    ? new Date(toDate.getFullYear(), toDate.getMonth(), toDate.getDate())
    : null;
 
  // Check tabValue filters
  if (tabValue === 1 && ticket.state !== "New") return false;
  if (tabValue === 2 && ticket.state !== "In Progress") return false;
  if (tabValue === 3 && ticket.state !== "Resolved") return false;
  if (tabValue === 4 && ticket.state !== "Closed") return false;
 
  // Check search query filter
  if (searchQuery && !ticket.incidentId.includes(searchQuery)) return false;
 
  // Check date filters
  if (normalizedFromDate && normalizedCreatedDate < normalizedFromDate)
    return false; // Compare "Created" with "From Date"
  if (normalizedToDate && normalizedCreatedDate > normalizedToDate)
    return false; // Compare "Created" with "To Date"
 
  return true; // If all conditions pass, include the ticket
});

  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });

  const handleSort = (columnKey) => {
    let direction = "asc";
    if (sortConfig.key === columnKey && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key: columnKey, direction });
  };

  const sortedTickets = [...filteredTickets].sort((a, b) => {
    if (!sortConfig.key) return 0; // No sorting applied
    const aValue = a[sortConfig.key] || ""; // Handle undefined values
    const bValue = b[sortConfig.key] || ""; // Handle undefined values

    if (sortConfig.direction === "asc") {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
    } else {
      return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
    }
  });

  // Pagination logic
  const totalPages = Math.ceil(sortedTickets.length / rowsPerPage);
  const paginatedTickets = sortedTickets.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const handleAgenticAI = (ticket) => {
    showLoader();
    GetIncident(ticket.incidentId)
      .then((response) => {
        setSelectedTicket(response.data.message); // Store the ticket in global state
        navigate(`/AgenticAI/${ticket.incidentId}`);
        hideLoader();
      })
      .catch((error) => {
        toast.error(error.response.data.message);
        hideLoader();
      });
  };

  const handleRefresh = () => {
    showLoader();
    GetAllIncidents()
      .then((response) => {
        setIncidents(response.data.message);
        hideLoader();
      })
      .catch((error) => {
        toast.error(error.response.data.message);
        hideLoader();
      });
  };



  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",

          height: "100vh",
          width: "100%",
        }}
      >
        {/* Header */}

        <Box sx={{ padding: 1 }}>
          <Box
            sx={{
              padding: 2,
              display: "flex",
              flexDirection: "column",
              backgroundColor: "rgb(255, 255, 255)",
              borderRadius: "10px",
            }}
          >
            {/* Title and Filters */}
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}
            >
              <Typography
                sx={{
                  color: "#B1125B",
                  fontWeight: "bold",
                  fontSize: "20px",
                }}
              >
                Incidents
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {/* Search Box */}
                <TextField
                  variant="outlined"
                  size="small"
                  placeholder="Search Incidents"
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      borderRadius: "10px",
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
                  InputProps={{
                    startAdornment: (
                      <SearchIcon sx={{ color: "rgba(0, 0, 0, 0.6)" }} />
                    ),
                  }}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />

                {/* Refresh Button */}
                <Tooltip title="Refresh">
                  <IconButton
                    onClick={handleRefresh}
                    color="primary"
                    aria-label="refresh"
                    sx={{
                      backgroundColor: "#B1125B",
                      color: "white",
                      "&:hover": {
                        backgroundColor: "#D81B60", // Darker orange on hover
                      },
                    }}
                  >
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            {/* Status Cards */}
            <Grid
              container
              spacing={2}
              sx={{ padding: "10px 0px 10px 0px", width: "100%" }}
            >
              {["New", "In Progress", "Resolved", "Closed"].map(
                (status, index) => (
                  <Grid item size={3} key={index}>
                    <Card
                      sx={{
                        height: "90%",
                        borderRadius: "10px",
                        cursor: "pointer",

                        boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.2)", // Add shadow
                        transition: "transform 0.2s, box-shadow 0.2s", // Add smooth hover effect
                        "&:hover": {
                          transform: "scale(1.05)", // Slightly scale up on hover
                          boxShadow: "0px 6px 15px rgba(0, 0, 0, 0.3)", // Increase shadow on hover
                        },
                      }}
                      onClick={() => handleCardClick(status)}
                    >
                      <CardContent>
                        <Box
                          sx={{ display: "flex", alignItems: "center", gap: 1 }}
                        >
                          {/* Dot for status */}
                          <Box
                            sx={{
                              width: 10,
                              height: 10,
                              borderRadius: "50%",
                              backgroundColor: getStatusColor(status),
                            }}
                          />
                          <Typography variant="h6">{status}</Typography>
                        </Box>
                        <Typography variant="h4">
                          {
                            incidents.filter(
                              (ticket) => ticket.state === status
                            ).length
                          }
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )
              )}
            </Grid>
            {/* Tabs */}
            <Box
              sx={{
                display: "flex",
                flexDirection: "row",
                flexWrap: "wrap",
                justifyContent: "space-between",
                gap: 2,
                "@media (max-width: 600px)": {
                  flexDirection: "column", // Stack elements vertically on small screens
                  alignItems: "flex-start",
                },
              }}
            >
              {/* Tabs Section */}
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                sx={{
                  borderBottom: 1,
                  borderColor: "divider",
                  "& .MuiTabs-indicator": {
                    backgroundColor: "#B1125B",
                  },
                }}
              >
                {["All", "New", "In Progress", "Resolved", "Closed"].map(
                  (label, index) => (
                    <Tab
                      key={label}
                      label={label}
                      sx={{
                        fontSize: "0.875rem",
                        fontWeight: "bold",
                        color: tabValue === index ? "#B1125B" : "inherit",
                        "&.Mui-selected": {
                          color: "#B1125B",
                        },
                      }}
                    />
                  )
                )}
              </Tabs>

              {/* Date Pickers Section */}
              <Box
                sx={{
                  display: "flex",
                  gap: 2,
                  flexWrap: "wrap",
                  alignItems: "center",
                  justifyContent: "flex-start",
                }}
              >
                <DatePicker
                  label="From Date"
                  value={fromDate}
                  maxDate = {formattedTodayDate}
                  onChange={(newValue) => {
                    setFromDate(newValue);
                    setToDate(null); // Reset "To Date" when "From Date" changes
                  }}
                  format="dd-MM-yyyy"
                  renderInput={(params) => (
                    <TextField {...params} size="small" />
                  )}
                />

                {/* To Date Picker */}
                <DatePicker
                  label="To Date"
                  value={toDate}
                  onChange={(newValue) => setToDate(newValue)}
                  format="dd-MM-yyyy"
                  minDate={fromDate} // Set the minimum selectable date to the "From Date"
                  maxDate = {formattedTodayDate}
                  disabled={!fromDate} // Disable "To Date" picker if "From Date" is not selected
                  renderInput={(params) => (
                    <TextField {...params} size="small" />
                  )}
                />
                <Tooltip title="Clear Dates">
                  <IconButton onClick={handleClearDates}>
                    <ClearIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            {/* Ticket List Table */}
            <TableContainer
              component={Paper}
              sx={{ marginTop: 2, borderRadius: "10px" }}
            >
              <Table>
                <TableHead sx={{ backgroundColor: "#B1125B" }}>
                  <TableRow sx={{ height: "2rem" }}>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      <TableSortLabel
                        active={sortConfig.key === "incidentId"}
                        direction={
                          sortConfig.key === "incidentId"
                            ? sortConfig.direction
                            : "asc"
                        }
                        onClick={() => handleSort("incidentId")}
                      >
                        Incident ID
                      </TableSortLabel>
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      Short Description
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      Configuration Item
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      <TableSortLabel
                        active={sortConfig.key === "createdOn"}
                        direction={
                          sortConfig.key === "createdOn"
                            ? sortConfig.direction
                            : "asc"
                        }
                        onClick={() => handleSort("createdOn")}
                      >
                        Created On
                      </TableSortLabel>
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      State / Work Notes
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      MIM Status
                    </TableCell>
                    <TableCell
                      sx={{
                        color: "white",
                        padding: "0.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      Information
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedTickets.length > 0 ? (
                    paginatedTickets.map((ticket, index) => (
                      <TableRow
                        key={index}
                        sx={{
                          height: "55px",
                          cursor: "pointer",
                          transition: "background-color 0.3s ease",
                          opacity:
                            ticket.agentRunStatus === "Incident Received" ||
                            ticket.agentRunStatus === "Incident Processing" ||
                            ticket.agentRunStatus === "CI Unavailable"
                              ? 0.5
                              : 1,
                          pointerEvents:
                            ticket.agentRunStatus === "Incident Processing" ||
                            ticket.agentRunStatus === "Incident Received" ||
                            ticket.agentRunStatus === "CI Unavailable"
                              ? "none"
                              : "auto",
                          "&:hover": {
                            backgroundColor: "rgba(0, 0, 0, 0.05)",
                          },
                        }}
                        onClick={() => {
                          handleAgenticAI(ticket);
                        }}
                      >
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          {ticket.incidentId || "NIL"}
                        </TableCell>
                        <TableCell
                          sx={{
                            whiteSpace: "normal",
                            wordBreak: "break-word",
                            maxWidth: "200px",
                            padding: "4px 8px",
                          }}
                        >
                          {ticket.shortDescription || "NIL"}
                          <Tooltip title="View Short Description">
                            <IconButton
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDialogOpen(
                                  "Short Description & Description",
                                  {
                                    "Short Description":
                                      ticket.shortDescription || "NIL",
                                    Description: ticket.description || "NIL",
                                  }
                                );
                              }}
                            >
                              <VisibilityIcon
                                fontSize="small"
                                style={{ color: "grey" }}
                              />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          {ticket.configurationItem || "NIL"}
                        </TableCell>
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          {ticket.createdOn || "NIL"}
                        </TableCell>
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Box
                              sx={{
                                width: 10,
                                height: 10,
                                borderRadius: "50%",
                                backgroundColor: getStatusColor(ticket.state),
                              }}
                            />
                            {ticket.state || "NIL"}
                            {ticket.state === "In Progress" && (
                              <Tooltip title="View Work Notes">
                                <IconButton
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDialogOpen("Work Notes & Comments", {
                                      "Work Notes":
                                        ticket["Work notes"] || "NIL",
                                      "Comments / Work Notes":
                                        ticket["Comments and Work notes"] ||
                                        "NIL",
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
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          {ticket.agentRunStatus || "NIL"}
                        </TableCell>
                        <TableCell
                          sx={{
                            padding: "4px 8px",
                            lineHeight: "1.2",
                          }}
                        >
                          <Tooltip title="View Details">
                            <IconButton
                              onClick={(e) => {
                                e.stopPropagation();
                                // const filteredData = Object.keys(ticket)
                                //   .filter(
                                //     (key) =>
                                //       ![
                                //         "Short description",
                                //         "Description",
                                //         "Work notes",
                                //         "Comments and Work notes",
                                //       ].includes(key)
                                //   )
                                //   .reduce((obj, key) => {
                                //     obj[key] = ticket[key] || "NIL";
                                //     return obj;
                                //   }, {});

                                handleDialogOpen(
                                  "Ticket Details",{
                                    "Incident ID" : ticket.incidentId,
                                    "Short Description" : ticket.shortDescription,
                                    "Description" : ticket.description,
                                    "Created on" : ticket.createdOn,
                                    "Open Since" : ticket.openSince,
                                    "State" : ticket.state,
                                    "Agent Run Status" : ticket.agentRunStatus,
                                     "Priority" : ticket.priority,
                                    "Configuration Item" : ticket.configurationItem,
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
                        No tickets found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            {/* Pagination */}
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: 2,
              }}
            >
              {/* Left End: Pagination Controls */}
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <IconButton
                  disabled={currentPage === 1 || paginatedTickets.length === 0}
                  onClick={() => setCurrentPage((prev) => prev - 1)}
                >
                  <ArrowBackIosIcon sx={{ fontSize: "16px" }} />
                </IconButton>
                <Typography variant="body2">
                  Page {paginatedTickets.length === 0 ? 0 : currentPage} of{" "}
                  {totalPages}
                </Typography>
                <IconButton
                  disabled={
                    currentPage === totalPages || paginatedTickets.length === 0
                  }
                  onClick={() => setCurrentPage((prev) => prev + 1)}
                >
                  <ArrowForwardIosIcon sx={{ fontSize: "16px" }} />
                </IconButton>
              </Box>

              {/* Right End: Results Count */}
              <Typography variant="body2">
                Showing {paginatedTickets.length} of {filteredTickets.length}{" "}
                results
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>
      <DataViewer
        open={dialogOpen}
        onClose={handleDialogClose}
        title={dialogTitle}
        content={dialogContent}
      />
    </LocalizationProvider>
  );
};

export default Dashboard;

