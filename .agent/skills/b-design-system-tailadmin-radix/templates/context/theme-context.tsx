import * as React from "react";

export type ThemeMode = "light" | "dark" | "auto";
export type ActiveTheme = "light" | "dark";

export type ThemeContextType = {
  theme: ActiveTheme;
  selectedTheme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
};

const ThemeContext = React.createContext<ThemeContextType | undefined>(
  undefined,
);

function resolveActiveTheme(selectedTheme: ThemeMode): ActiveTheme {
  if (selectedTheme === "auto") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return selectedTheme;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [selectedTheme, setSelectedThemeState] =
    React.useState<ThemeMode>("light");
  const [theme, setThemeState] = React.useState<ActiveTheme>("light");
  const [isInitialized, setIsInitialized] = React.useState(false);

  React.useEffect(() => {
    const savedTheme = localStorage.getItem("theme") as ThemeMode | null;
    const initialTheme = savedTheme ?? "light";
    setSelectedThemeState(initialTheme);
    setThemeState(resolveActiveTheme(initialTheme));
    setIsInitialized(true);
  }, []);

  React.useEffect(() => {
    if (!isInitialized) return;

    localStorage.setItem("theme", selectedTheme);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = () => {
      setThemeState(resolveActiveTheme(selectedTheme));
    };

    handleChange();

    if (selectedTheme === "auto") {
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [selectedTheme, isInitialized]);

  React.useEffect(() => {
    if (!isInitialized) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme, isInitialized]);

  const setTheme = React.useCallback((newTheme: ThemeMode) => {
    setSelectedThemeState(newTheme);
  }, []);

  const toggleTheme = React.useCallback(() => {
    setSelectedThemeState((prev) => {
      const resolved = resolveActiveTheme(prev);
      return resolved === "light" ? "dark" : "light";
    });
  }, []);

  const value = React.useMemo<ThemeContextType>(
    () => ({ theme, selectedTheme, setTheme, toggleTheme }),
    [selectedTheme, setTheme, theme, toggleTheme],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = React.useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
