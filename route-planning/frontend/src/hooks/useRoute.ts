import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@chakra-ui/react';

import { RouteRequest, RouteResponse, RouteListResponse } from '../types';
import * as routeService from '../services/routeService';

export const useCalculateRoute = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RouteRequest) => routeService.calculateRoute(request),
    onSuccess: (data: RouteResponse) => {
      toast({
        title: 'Sukces',
        description: 'Trasa została obliczona pomyślnie',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      // Invalidate route list
      queryClient.invalidateQueries({ queryKey: ['routes'] });
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.message || 'Błąd podczas obliczania trasy',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};

export const useRoute = (routeId: string) => {
  return useQuery({
    queryKey: ['route', routeId],
    queryFn: () => routeService.getRoute(routeId),
    enabled: !!routeId,
  });
};

export const useRoutes = (page: number = 0, limit: number = 10) => {
  return useQuery({
    queryKey: ['routes', page, limit],
    queryFn: () => routeService.getRoutes(page * limit, limit),
    keepPreviousData: true,
  });
};

export const useDeleteRoute = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (routeId: string) => routeService.deleteRoute(routeId),
    onSuccess: () => {
      toast({
        title: 'Sukces',
        description: 'Trasa została usunięta',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['routes'] });
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.message || 'Błąd podczas usuwania trasy',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};

export const useRouteExport = () => {
  const toast = useToast();

  return useMutation({
    mutationFn: (routeId: string) => routeService.exportRouteToGPX(routeId),
    onSuccess: (data: Blob, variables: string) => {
      // Create download link
      const url = window.URL.createObjectURL(data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `route_${variables}.gpx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Sukces',
        description: 'Trasa została wyeksportowana do pliku GPX',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Błąd',
        description: error.message || 'Błąd podczas eksportu trasy',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};

export const useRouteStatistics = () => {
  return useQuery({
    queryKey: ['route-statistics'],
    queryFn: () => routeService.getRouteStatistics(),
  });
};

// Hook do zarządzania stanem wybranej trasy
export const useSelectedRoute = () => {
  const [selectedRoute, setSelectedRoute] = useState<RouteResponse | null>(null);

  const selectRoute = useCallback((route: RouteResponse) => {
    setSelectedRoute(route);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedRoute(null);
  }, []);

  return {
    selectedRoute,
    selectRoute,
    clearSelection,
  };
};

// Hook do zarządzania lokalnym stanem tras
export const useLocalRoutes = () => {
  const [routes, setRoutes] = useState<RouteResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addRoute = useCallback((route: RouteResponse) => {
    setRoutes(prev => [route, ...prev]);
  }, []);

  const removeRoute = useCallback((routeId: string) => {
    setRoutes(prev => prev.filter(route => route.id !== routeId));
  }, []);

  const updateRoute = useCallback((routeId: string, updatedRoute: Partial<RouteResponse>) => {
    setRoutes(prev =>
      prev.map(route =>
        route.id === routeId ? { ...route, ...updatedRoute } : route
      )
    );
  }, []);

  const clearRoutes = useCallback(() => {
    setRoutes([]);
  }, []);

  return {
    routes,
    isLoading,
    setIsLoading,
    addRoute,
    removeRoute,
    updateRoute,
    clearRoutes,
  };
};
