import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import theme from './theme';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import RouteCalculatorPage from './pages/RouteCalculatorPage';
import RouteDetailsPage from './pages/RouteDetailsPage';
import RouteListPage from './pages/RouteListPage';
import WeatherPage from './pages/WeatherPage';
import AboutPage from './pages/AboutPage';

// Utwórz klienta React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minut
    },
  },
});

const App: React.FC = () => {
  return (
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/calculator" element={<RouteCalculatorPage />} />
              <Route path="/routes" element={<RouteListPage />} />
              <Route path="/routes/:routeId" element={<RouteDetailsPage />} />
              <Route path="/weather" element={<WeatherPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </Layout>
        </Router>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ChakraProvider>
  );
};

export default App;
