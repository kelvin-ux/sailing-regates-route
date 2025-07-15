import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  VStack,
  HStack,
  Text,
  Switch,
  FormErrorMessage,
  useToast,
} from '@chakra-ui/react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

import { RouteRequest, BoatProfile } from '../types';
import { useBoatProfiles } from '../hooks/useBoatProfiles';

// Schemat walidacji
const routeSchema = yup.object({
  start: yup.object({
    lat: yup.number().min(-90).max(90).required('Szerokość geograficzna jest wymagana'),
    lon: yup.number().min(-180).max(180).required('Długość geograficzna jest wymagana'),
  }).required(),
  end: yup.object({
    lat: yup.number().min(-90).max(90).required('Szerokość geograficzna jest wymagana'),
    lon: yup.number().min(-180).max(180).required('Długość geograficzna jest wymagana'),
  }).required(),
  grid_resolution_nm: yup.number().min(0.1).max(2.0).required(),
  corridor_margin_nm: yup.number().min(0.5).max(10.0).required(),
  max_calculation_time: yup.number().min(5).max(120).required(),
  alternatives_count: yup.number().min(1).max(5).required(),
  use_weather_routing: yup.boolean().required(),
});

interface RouteFormProps {
  onSubmit: (data: RouteRequest) => void;
  isLoading?: boolean;
  initialData?: Partial<RouteRequest>;
}

const RouteForm: React.FC<RouteFormProps> = ({
  onSubmit,
  isLoading = false,
  initialData
}) => {
  const toast = useToast();
  const { data: boatProfiles } = useBoatProfiles();
  
  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset
  } = useForm<RouteRequest>({
    resolver: yupResolver(routeSchema),
    defaultValues: {
      start: { lat: 54.52, lon: 18.55 },
      end: { lat: 54.48, lon: 18.65 },
      grid_resolution_nm: 0.5,
      corridor_margin_nm: 2.0,
      max_calculation_time: 30,
      alternatives_count: 1,
      use_weather_routing: true,
      ...initialData
    }
  });

  const watchedValues = watch();
  const [coordinateInput, setCoordinateInput] = useState({
    startLat: watchedValues.start.lat.toString(),
    startLon: watchedValues.start.lon.toString(),
    endLat: watchedValues.end.lat.toString(),
    endLon: watchedValues.end.lon.toString(),
  });

  // Aktualizuj formularz gdy zmieni się initialData
  useEffect(() => {
    if (initialData) {
      reset({ ...watchedValues, ...initialData });
    }
  }, [initialData, reset]);

  const handleCoordinateChange = (field: string, value: string) => {
    setCoordinateInput(prev => ({ ...prev, [field]: value }));
    
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      if (field === 'startLat') setValue('start.lat', numValue);
      if (field === 'startLon') setValue('start.lon', numValue);
      if (field === 'endLat') setValue('end.lat', numValue);
      if (field === 'endLon') setValue('end.lon', numValue);
    }
  };

  const handleQuickLocations = (location: 'gdansk' | 'gdynia' | 'sopot') => {
    const locations = {
      gdansk: { lat: 54.3520, lon: 18.6466 },
      gdynia: { lat: 54.5189, lon: 18.5305 },
      sopot: { lat: 54.4418, lon: 18.5601 },
    };
    
    const coords = locations[location];
    setValue('start.lat', coords.lat);
    setValue('start.lon', coords.lon);
    setCoordinateInput(prev => ({
      ...prev,
      startLat: coords.lat.toString(),
      startLon: coords.lon.toString(),
    }));
  };

  const onFormSubmit = (data: RouteRequest) => {
    try {
      onSubmit(data);
      toast({
        title: 'Obliczanie trasy',
        description: 'Rozpoczęto obliczanie optymalnej trasy...',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Błąd',
        description: 'Wystąpił błąd podczas wysyłania formularza',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Box p={4}>
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <VStack spacing={4} align="stretch">
          {/* Punkt startowy */}
          <Box>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              Punkt startowy
            </Text>
            <HStack spacing={2}>
              <Button size="sm" onClick={() => handleQuickLocations('gdansk')}>
                Gdańsk
              </Button>
              <Button size="sm" onClick={() => handleQuickLocations('gdynia')}>
                Gdynia
              </Button>
              <Button size="sm" onClick={() => handleQuickLocations('sopot')}>
                Sopot
              </Button>
            </HStack>
            <HStack spacing={2} mt={2}>
              <FormControl isInvalid={!!errors.start?.lat}>
                <FormLabel fontSize="sm">Szerokość</FormLabel>
                <Input
                  value={coordinateInput.startLat}
                  onChange={(e) => handleCoordinateChange('startLat', e.target.value)}
                  placeholder="54.52"
                />
                <FormErrorMessage>{errors.start?.lat?.message}</FormErrorMessage>
              </FormControl>
              <FormControl isInvalid={!!errors.start?.lon}>
                <FormLabel fontSize="sm">Długość</FormLabel>
                <Input
                  value={coordinateInput.startLon}
                  onChange={(e) => handleCoordinateChange('startLon', e.target.value)}
                  placeholder="18.55"
                />
                <FormErrorMessage>{errors.start?.lon?.message}</FormErrorMessage>
              </FormControl>
            </HStack>
          </Box>

          {/* Punkt końcowy */}
          <Box>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              Punkt końcowy
            </Text>
            <HStack spacing={2}>
              <FormControl isInvalid={!!errors.end?.lat}>
                <FormLabel fontSize="sm">Szerokość</FormLabel>
                <Input
                  value={coordinateInput.endLat}
                  onChange={(e) => handleCoordinateChange('endLat', e.target.value)}
                  placeholder="54.48"
                />
                <FormErrorMessage>{errors.end?.lat?.message}</FormErrorMessage>
              </FormControl>
              <FormControl isInvalid={!!errors.end?.lon}>
                <FormLabel fontSize="sm">Długość</FormLabel>
                <Input
                  value={coordinateInput.endLon}
                  onChange={(e) => handleCoordinateChange('endLon', e.target.value)}
                  placeholder="18.65"
                />
                <FormErrorMessage>{errors.end?.lon?.message}</FormErrorMessage>
              </FormControl>
            </HStack>
          </Box>

          {/* Parametry łodzi */}
          <Box>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              Parametry łodzi
            </Text>
            <Controller
              name="boat_profile_id"
              control={control}
              render={({ field }) => (
                <FormControl>
                  <FormLabel>Profil łodzi</FormLabel>
                  <Select {...field} placeholder="Wybierz profil łodzi">
                    {boatProfiles?.map((profile: BoatProfile) => (
                      <option key={profile.id} value={profile.id}>
                        {profile.name} ({profile.type})
                      </option>
                    ))}
                  </Select>
                </FormControl>
              )}
            />
            <Controller
              name="boat_type"
              control={control}
              render={({ field }) => (
                <FormControl mt={2}>
                  <FormLabel>Typ łodzi (alternatywnie)</FormLabel>
                  <Select {...field} placeholder="Wybierz typ łodzi">
                    <option value="monohull">Jednokadłubowiec</option>
                    <option value="catamaran">Katamaran</option>
                    <option value="trimaran">Trimaran</option>
                  </Select>
                </FormControl>
              )}
            />
          </Box>

          {/* Parametry obliczenia */}
          <Box>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              Parametry obliczenia
            </Text>
            <Controller
              name="grid_resolution_nm"
              control={control}
              render={({ field }) => (
                <FormControl isInvalid={!!errors.grid_resolution_nm}>
                  <FormLabel>Rozdzielczość siatki (NM)</FormLabel>
                  <NumberInput min={0.1} max={2.0} step={0.1} {...field}>
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <FormErrorMessage>{errors.grid_resolution_nm?.message}</FormErrorMessage>
                </FormControl>
              )}
            />
            
            <Controller
              name="corridor_margin_nm"
              control={control}
              render={({ field }) => (
                <FormControl isInvalid={!!errors.corridor_margin_nm} mt={2}>
                  <FormLabel>Margines korytarza (NM)</FormLabel>
                  <NumberInput min={0.5} max={10.0} step={0.5} {...field}>
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <FormErrorMessage>{errors.corridor_margin_nm?.message}</FormErrorMessage>
                </FormControl>
              )}
            />

            <Controller
              name="alternatives_count"
              control={control}
              render={({ field }) => (
                <FormControl isInvalid={!!errors.alternatives_count} mt={2}>
                  <FormLabel>Liczba alternatywnych tras</FormLabel>
                  <NumberInput min={1} max={5} step={1} {...field}>
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <FormErrorMessage>{errors.alternatives_count?.message}</FormErrorMessage>
                </FormControl>
              )}
            />

            <Controller
              name="max_calculation_time"
              control={control}
              render={({ field }) => (
                <FormControl isInvalid={!!errors.max_calculation_time} mt={2}>
                  <FormLabel>Maksymalny czas obliczenia (s)</FormLabel>
                  <NumberInput min={5} max={120} step={5} {...field}>
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                  <FormErrorMessage>{errors.max_calculation_time?.message}</FormErrorMessage>
                </FormControl>
              )}
            />
          </Box>

          {/* Opcje pogodowe */}
          <Box>
            <Text fontSize="lg" fontWeight="bold" mb={2}>
              Opcje pogodowe
            </Text>
            <Controller
              name="use_weather_routing"
              control={control}
              render={({ field }) => (
                <FormControl display="flex" alignItems="center">
                  <FormLabel mb={0}>Routing pogodowy</FormLabel>
                  <Switch {...field} isChecked={field.value} />
                </FormControl>
              )}
            />
          </Box>

          {/* Przycisk submit */}
          <Button
            type="submit"
            colorScheme="blue"
            size="lg"
            isLoading={isLoading}
            loadingText="Obliczanie..."
          >
            Oblicz trasę
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default RouteForm;
