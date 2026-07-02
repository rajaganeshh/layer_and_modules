import { createTheme } from "@mui/material/styles";

export const virginPalette = {
  primary: "#B1125B",
  primaryDark: "#7A003C",
  primarySoft: "#D81B60",
  backgroundTint: "#FCE7F1",
  textMain: "#231A20",
};

const virginTheme = createTheme({
  palette: {
    primary: {
      main: virginPalette.primary,
      dark: virginPalette.primaryDark,
      light: virginPalette.primarySoft,
      contrastText: "#FFFFFF",
    },
    background: {
      default: "#FFFFFF",
      paper: "#FFFFFF",
    },
    text: {
      primary: virginPalette.textMain,
    },
  },
  typography: {
    fontFamily: '"Barlow", "Segoe UI", "Helvetica Neue", Arial, sans-serif',
    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },
});

export default virginTheme;