import { Route, Routes } from "react-router-dom";
import CreateProfilePage from "./pages/CreateProfilePage";
import HistoryPage from "./pages/HistoryPage";
import MainPage from "./pages/MainPage";
import SelectProfilePage from "./pages/SelectProfilePage";
import StructureBuilderPage from "./pages/StructureBuilderPage";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/structure" element={<StructureBuilderPage />} />
      <Route path="/profiles/select" element={<SelectProfilePage />} />
      <Route path="/profiles/new" element={<CreateProfilePage />} />
    </Routes>
  );
};

export default App;
