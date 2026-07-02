import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
} from "@mui/material";

const ConfirmationDialog = ({ open, title, message, onConfirm, onCancel }) => {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirmation-dialog-title"
      aria-describedby="confirmation-dialog-description"
      sx={{
        "& .MuiDialog-paper": {
          borderRadius: "12px", // Rounded corners for the dialog
          padding: "16px", // Add padding for better spacing
        },
      }}
    >
      <DialogTitle
        id="confirmation-dialog-title"
        sx={{
          fontWeight: "bold",
          textAlign: "center",
          color: "#B1125B", // Orange color for the title
        }}
      >
        {title}
      </DialogTitle>
      <DialogContent>
        <Typography
          id="confirmation-dialog-description"
          sx={{
            textAlign: "center",
            color: "#333333", // Dark gray for the message text
            fontSize: "16px",
          }}
        >
          {message}
        </Typography>
      </DialogContent>
      <DialogActions sx={{ justifyContent: "center", gap: "16px" }}>
        <Button
          onClick={onCancel}
          variant="outlined"
          sx={{
            borderColor: "#B1125B", // Orange border for outlined button
            color: "#B1125B", // Orange text color
            "&:hover": {
              backgroundColor: "rgba(177, 18, 91, 0.12)", // Light orange hover effect
            },
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          sx={{
            backgroundColor: "#B1125B", // Orange background for primary button
            color: "#FFFFFF", // White text color
            "&:hover": {
              backgroundColor: "#7A003C", // Darker orange on hover
            },
          }}
        >
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmationDialog;

