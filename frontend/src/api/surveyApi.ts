import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { APP_API_PREFIX } from '../config/api';

export const surveyApi = createApi({
  reducerPath: 'surveyApi',
  baseQuery: fetchBaseQuery({ baseUrl: APP_API_PREFIX }),
  tagTypes: ['Survey', 'Frame'],
  endpoints: (builder) => ({
    getSurveys: builder.query({
      query: (params) => ({
        url: '/surveys',
        params,
      }),
      providesTags: ['Survey'],
    }),
    getSurveyById: builder.query({
      query: (id: string) => `/surveys/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Survey', id }],
    }),
    getSurveyFrames: builder.query({
      query: ({ surveyId, page = 1, limit = 50 }) => ({
        url: `/surveys/${surveyId}/frames`,
        params: { page, limit },
      }),
      providesTags: ['Frame'],
    }),
    uploadSurvey: builder.mutation({
      query: (formData: FormData) => ({
        url: '/surveys',
        method: 'POST',
        body: formData,
      }),
      invalidatesTags: ['Survey'],
    }),
  }),
});

export const {
  useGetSurveysQuery,
  useGetSurveyByIdQuery,
  useGetSurveyFramesQuery,
  useUploadSurveyMutation,
} = surveyApi;
