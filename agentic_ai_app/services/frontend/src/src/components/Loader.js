import React from "react";
import { Box } from "@mui/material";
import { useGlobalContext } from "../Global/GlobalContext";
 
const Loader = () => {
      const { loading } = useGlobalContext();

  if (!loading) return null;
  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        backgroundColor: "rgba(0, 0, 0, 0.5)", // Semi-transparent overlay
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 9999,
      }}
    >
      <Box sx={{ display: "flex", gap: "8px" }}>
        {[...Array(4)].map((_, i) => (
          <Box
            key={i}
            sx={{
              width: "12px",
              height: "12px",
              backgroundColor: "#ffffff",
              borderRadius: "50%",
              animation: "jump 1.5s infinite ease-in-out",
              animationDelay: `${i * 0.2}s`,
              "@keyframes jump": {
                "0%, 100%": { transform: "translateY(0)" },
                "50%": { transform: "translateY(-10px)" },
              },
            }}
          />
        ))}
      </Box>
    </Box>
  );
};
 
export default Loader;
