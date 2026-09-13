import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { AUTH_API_PREFIX } from '../config/api';

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({ baseUrl: AUTH_API_PREFIX }),
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation({
      query: (data) => ({
        url: '/register',
        method: 'POST',
        body: data,
      }),
    }),
    refreshToken: builder.mutation({
      query: (data) => ({
        url: '/refresh',
        method: 'POST',
        body: data,
      }),
    }),
    getCurrentUser: builder.query({
      query: () => '/me',
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
} = authApi;
