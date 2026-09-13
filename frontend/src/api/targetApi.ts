import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { APP_API_PREFIX } from '../config/api';

export const targetApi = createApi({
  reducerPath: 'targetApi',
  baseQuery: fetchBaseQuery({ baseUrl: APP_API_PREFIX }),
  tagTypes: ['Target'],
  endpoints: (builder) => ({
    getTargets: builder.query({
      query: (params) => ({
        url: '/targets',
        params,
      }),
      providesTags: ['Target'],
    }),
    getTargetById: builder.query({
      query: (id: string) => `/targets/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Target', id }],
    }),
  }),
});

export const {
  useGetTargetsQuery,
  useGetTargetByIdQuery,
} = targetApi;
