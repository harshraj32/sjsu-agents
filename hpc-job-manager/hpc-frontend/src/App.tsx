import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { UserProvider } from "./contexts/UserContext.tsx" ;  // Import UserProvider
import CreateJob from "./pages/CreateJob";
import MonitorJobs from "./pages/MonitorJobs";

const App = () => {
  return (
    <UserProvider>
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-blue-600 p-4 text-white flex justify-between">
        <div className="text-xl font-bold">HPC Job Manager</div>
        <div className="space-x-4">
        
          <Link to="/create">Create Job</Link>
          <Link to="/monitor">Monitor Jobs</Link>
        </div>
      </nav>

      <div className="p-6">
        <Routes>
          <Route path="/create" element={<CreateJob />} />
          <Route path="/monitor" element={<MonitorJobs />} />
        </Routes>
      </div>
    </div>
    </UserProvider>
  );
};

export default App;
