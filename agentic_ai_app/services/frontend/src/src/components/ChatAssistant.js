import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  IconButton,
  Typography,
  Button,
  TextField,
  Stack,
  CircularProgress,
} from "@mui/material";
import { Close, Send } from "@mui/icons-material";
import ChangeRequests from "./ChatData"; // Import the ChangeRequests component
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import mimImage from "../assets/mim_Image.png"
import { ChatAgent } from "../services/ApiCalls";
import { toast } from "react-toastify";
const ChatAssistant = ({ isOpen, onClose, selectedTicket }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false); // State for loading indicator
  const [showOptions, setShowOptions] = useState(true); // State to toggle the options
  const chatBoxRef = useRef(null); // Ref for auto-scrolling

  // Function to scroll to the bottom of the chat
  const scrollToBottom = () => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  };

  // Automatically scroll to the bottom when messages or components are updated
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

const handleSendMessage = (data) => {
  const { message = "", option = "" } = data; // Destructure with default values
  const trimmedMessage = message.trim();
 
  setInputMessage("")

  setIsLoading(true);

  // Prepare the user message
  const userMessage = {
    role: "user",
    message: trimmedMessage || option, // Use message if available, otherwise use option
  };

  // Prepare the params
  let params = {
    inc_id: selectedTicket?.ticketDetails?.incidentId || "",
    user_message: userMessage,
  };

  // Add the user message to the messages state
  setMessages((prev) => [
    ...prev,
    { role: "user", text: option || trimmedMessage }, // Use option if available, otherwise use message
  ]);

  // Call the ChatAgent API
  ChatAgent(params)
    .then((response) => {
      setIsLoading(false);

      // Add the assistant's response to the messages state
      if (response.data.message) {
        setMessages((prev) => [
          ...prev,
          {
            role: response.data.message.role,
            text: response.data.message.message,
          },
        ]);
        setInputMessage(""); // Clear the input field
      }

      // If the response contains additional content, add it as a component
      if (response.data.message.content?.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "component",
            component: (
              <ChangeRequests value={option} data={response.data.message.content} />
            ),
          },
        ]);
      }
    })
    .catch((error) => {
      toast.error(error.response?.data?.message || "An error occurred");
      setIsLoading(false);
    });
};

  const handleKeyDown = (e) => {
    if(e.key === "Enter"){
      e.preventDefault()
      handleSendMessage({message:inputMessage})
      setInputMessage("")
    }
  }

  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        right: isOpen ? 0 : "-30%", // Slide in/out based on `isOpen`
        width: "30%",
        height: "100%",
        backgroundColor: "white",
        boxShadow: "-4px 0px 10px rgba(0, 0, 0, 0.2)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        transition: "right 0.3s ease", // Smooth sliding animation
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px",
          backgroundColor: "white",
          height: "3rem",
        }}
      >
        <Typography variant="h6" sx={{ color: "black", fontWeight: "bold" }}>
          Incident Chat
        </Typography>
        <IconButton onClick={onClose}>
          <Close sx={{ color: "black" }} />
        </IconButton>
      </Box>

      {/* Chat Content */}
      <Box
        ref={chatBoxRef} // Attach the ref for auto-scrolling
        sx={{
          flex: 1,
          padding: "16px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}
      >
        {/* Incident Details */}
        <Box
          sx={{
            padding: "8px",
            border: "1px solid #B1125B",
            borderRadius: "8px",
            backgroundColor: "#FCE7F1",
          }}
        >
          <Typography variant="body2">
            <strong>Incident Details:</strong>{" "}
            {selectedTicket?.ticketDetails.shortDescription}
          </Typography>
        </Box>

        {/* Messages */}
        {messages.map((message, index) => (
  <Box
    key={index}
    sx={{
      display: "flex",
      alignItems: "center",
      justifyContent: message.role === "user" ? "flex-end" : message.role === "assistant" ? "flex-start" : "center", // User: right-aligned, Assistant: left-aligned, Component: center
      marginBottom: "8px", // Add spacing between messages
      
    }}
  >
    {/* Show the assistant image on the left for assistant messages */}
    {message.role === "assistant" && (
      <Box
        component="img"
        src={mimImage} // Replace with the actual path to the assistant image
        alt="Assistant"
        sx={{
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          marginRight: "8px", // Add spacing between the image and the text
        }}
      />
    )}

    {/* Message Box */}
    {message.role !== "component" && (
      <Box
        sx={{
          maxWidth: "70%",
          padding: "8px",
          borderRadius: "8px",
          backgroundColor: "transparent", // No background for messages
      color: message.role === "user" ? "white" : "black",
          whiteSpace: "pre-wrap", // Preserve line breaks in text
           backgroundColor:
                message.role === "user"
                  ? "#B1125B"
                  : message.role === "assistant"
                  ? "#f1f1f1"
                  : "transparent", // Transparent for components

        }}
      >
        <Typography variant="body2">{message.text}</Typography>
      </Box>
    )}

    {/* Show the user icon on the right for user messages */}
     {message.role === "user" && (
      <AccountCircleIcon
        sx={{
          fontSize: "32px", // Adjust size of the icon
          marginLeft: "2px", // Add spacing between the text and the icon
          color: "grey", // Optional: Set a color for the user icon
        }}
      />
    )}

    {/* Render the component directly if role is "component" */}
    {message.role === "component" && message.component}
  </Box>
))}

        {/* Loading Indicator */}
        {isLoading && (
           <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-start",
                  alignItems: "center",
                  padding: "8px",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    gap: "4px",
                  }}
                >
                  <Box
                    sx={{
                      width: "8px",
                      height: "8px",
                      backgroundColor: "gray",
                      borderRadius: "50%",
                      animation: "dot-flash 1.4s infinite",
                      animationDelay: "0s",
                    }}
                  />
                  <Box
                    sx={{
                      width: "8px",
                      height: "8px",
                      backgroundColor: "gray",
                      borderRadius: "50%",
                      animation: "dot-flash 1.4s infinite",
                      animationDelay: "0.2s",
                    }}
                  />
                  <Box
                    sx={{
                      width: "8px",
                      height: "8px",
                      backgroundColor: "gray",
                      borderRadius: "50%",
                      animation: "dot-flash 1.4s infinite",
                      animationDelay: "0.4s",
                    }}
                  />
                </Box>
              </Box>
        )}

        {/* Options */}
        {showOptions && !isLoading && (
          <Stack direction="row" spacing={0.5}>
            {["Recent Changes", "Recent Incidents", "Knowledge Articles"].map(
              (option) => (
                <Button
                  key={option}
                  variant="outlined"
                  sx={{
                    borderColor: "#B1125B",
                    color: "#B1125B",
                    textTransform: "none",
                    width: "100%",
                    fontSize: "12px",
                    borderRadius: "15px",
                  }}
                  onClick={() => handleSendMessage({option:option})}
                >
                  {option}
                </Button>
              )
            )}
          </Stack>
        )}
      </Box>

      {/* Input Field */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          padding: "8px",
          borderTop: "1px solid #ddd",
        }}
        onKeyDown = {handleKeyDown}
      >
        <TextField
          fullWidth
          variant="outlined"
          size="small"
          placeholder="Type your message..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: "50px",
            },
          }}
        />
        <IconButton
          onClick={() => handleSendMessage({message:inputMessage})}
          sx={{ marginLeft: 1, backgroundColor: "#B1125B", color: "white" }}
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  );
};

export default ChatAssistant;
