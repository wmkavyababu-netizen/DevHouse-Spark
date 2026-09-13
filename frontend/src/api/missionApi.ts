import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { APP_API_PREFIX } from '../config/api';

export const missionApi = createApi({
  reducerPath: 'missionApi',
  baseQuery: fetchBaseQuery({ baseUrl: APP_API_PREFIX }),
  tagTypes: ['Mission'],
  endpoints: (builder) => ({
    getMissions: builder.query({
      query: (params) => ({
        url: '/missions',
        params,
      }),
      providesTags: ['Mission'],
    }),
    getMissionById: builder.query({
      query: (id: string) => `/missions/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Mission', id }],
    }),
  }),
});

export const {
  useGetMissionsQuery,
  useGetMissionByIdQuery,
} = missionApi;
