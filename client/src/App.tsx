import { Route, Routes } from "react-router-dom";
import HistoryPage from "./pages/HistoryPage";
import MainPage from "./pages/MainPage";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/history" element={<HistoryPage />} />
    </Routes>
  );
};

export default App;

