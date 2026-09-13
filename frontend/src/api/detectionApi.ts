import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { APP_API_PREFIX } from '../config/api';

export const detectionApi = createApi({
  reducerPath: 'detectionApi',
  baseQuery: fetchBaseQuery({ baseUrl: APP_API_PREFIX }),
  tagTypes: ['Detection'],
  endpoints: (builder) => ({
    getDetectionsByFrame: builder.query({
      query: (frameId: string) => `/frames/${frameId}/detections`,
      providesTags: ['Detection'],
    }),
    getDetectionDetails: builder.query({
      query: (detectionId: string) => `/detections/${detectionId}`,
    }),
  }),
});

export const {
  useGetDetectionsByFrameQuery,
  useGetDetectionDetailsQuery,
} = detectionApi;
