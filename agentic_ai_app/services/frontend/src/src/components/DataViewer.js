import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,

  Box,
  Typography,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

export const DataViewer = ({ open, onClose, title = '', content }) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm" // Set the maximum width to "md" (medium size)
      fullWidth // Ensures the dialog takes up the full width of the container
      sx={{
        "& .MuiDialog-paper": {
          width: "900px", // Custom width for the dialog
          maxWidth: "none", // Disable the default maxWidth constraint
        },
      }}
    >
      <DialogTitle
        sx={{
          fontWeight: "bold",
          color: "#B1125B",
          display: "flex", // Use flexbox to align title and close icon
          justifyContent: "space-between", // Space out title and close icon
          alignItems: "center", // Vertically align items
        }}
      >
        {title}
        <IconButton onClick={onClose} sx={{ color: "#B1125B" }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        {Object.entries(content).map(([key, value]) => (
          <Box
            key={key}
            sx={{
              display: "flex",
              alignItems: "flex-start", // Align items to the top
              marginBottom: "12px", // Add spacing between rows
            }}
          >
            {/* Key (Heading) */}
            <Typography
              variant="body1"
              sx={{
                fontWeight: "bold",
                minWidth: "250px", // Fixed width for the key column
                textAlign: "left", // Align text to the left
              }}
            >
              {key}
            </Typography>

            {/* Colon */}
            <Typography
              variant="body1"
              sx={{
                fontWeight: "bold",
                marginRight: "8px", // Add spacing between colon and value
              }}
            >
              :
            </Typography>

            {/* Value */}
            <Typography
              variant="body1"
              sx={{
                flex: 1, // Allow the value to take up remaining space
                  whiteSpace: "pre-line", // Interpret \n as line breaks
                wordBreak: "break-word",
                
              }}
            >
              {value}
            </Typography>
          </Box>
        ))}
      </DialogContent>
    </Dialog>
  );
};

export const HolidayPopup = ({ open, onClose, title = '', content }) => {
    return (
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md" // Set the maximum width to "md" (medium size)
        fullWidth // Ensures the dialog takes up the full width of the container
        sx={{
          "& .MuiDialog-paper": {
            width: "700px", // Custom width for the dialog
            maxWidth: "none", // Disable the default maxWidth constraint
          
          },
        }}
      >
        <DialogTitle
          sx={{
            fontWeight: "bold",
            color: "#B1125B",
            display: "flex", // Use flexbox to align title and close icon
            justifyContent: "space-between", // Space out title and close icon
            alignItems: "center", // Vertically align items
          }}
        >
          {title}
          <IconButton onClick={onClose} sx={{ color: "#B1125B" }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
         <Box sx={{display:"flex"}}><Typography>{content}</Typography></Box>
        </DialogContent>
      </Dialog>
    );
  };

  export const ejholidays = "vaa holidays utilizes Salesforce as a key part of its operations, specifically for managing customer relationship management (CRM) and contact center technology. They are looking for a Salesforce Administrator with experience in a similar role, ideally with Salesforce Administrator or Advanced Administrator certifications. The role involves managing and maintaining Salesforce systems, performing upgrades, ensuring smooth integrations with other platforms, and managing relationships with third-party partners. "

