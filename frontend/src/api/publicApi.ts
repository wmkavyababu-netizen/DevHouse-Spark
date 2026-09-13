import { apiClient } from './client';

export interface PublicZone {
  id: string;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  status: string;
  description: string;
}

export interface AccessRequestPayload {
  fullName: string;
  officialEmail: string;
  organization: string;
  stakeholderRole: string;
  phoneNumber?: string;
  purposeOfAccess: string;
}

export interface AccessRequestResponse {
  requestId: string;
  status: string;
  message: string;
}

export const publicApi = {
  async getPublicZones(): Promise<PublicZone[]> {
    return apiClient<PublicZone[]>('/api/v1/public/zones');
  },

  async submitAccessRequest(payload: AccessRequestPayload): Promise<AccessRequestResponse> {
    return apiClient<AccessRequestResponse>('/api/v1/public/access-request', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
