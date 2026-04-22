import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HistoryProvider } from "@/contexts/HistoryContext";
import Index from "./pages/Index";
import MoodOfTheDay from "./pages/MoodOfTheDay";
import HelpMeWrite from "./pages/HelpMeWrite";
import JourneyThroughTime from "./pages/JourneyThroughTime";
import TreasuresOfWords from "./pages/TreasuresOfWords";
import PoetryInterpretation from "./pages/PoetryInterpretation";
import PoetryMemoryGame from "./pages/PoetryMemoryGame";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <HistoryProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/mood" element={<MoodOfTheDay />} />
            <Route path="/write" element={<HelpMeWrite />} />
            <Route path="/journey" element={<JourneyThroughTime />} />
            <Route path="/treasures" element={<TreasuresOfWords />} />
            <Route path="/interpret" element={<PoetryInterpretation />} />
            <Route path="/game" element={<PoetryMemoryGame />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </HistoryProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
