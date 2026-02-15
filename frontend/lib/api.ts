import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

// API Configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from storage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
      if (this.accessToken) {
        this.client.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`;
      }
    }

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;
        
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;
          
          if (this.refreshToken) {
            try {
              const response = await this.refreshAccessToken();
              if (response.data) {
                this.setTokens(response.data.access_token, response.data.refresh_token);
                originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              this.logout();
              window.location.href = '/auth/login';
            }
          } else {
            this.logout();
            window.location.href = '/auth/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
    this.client.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  isAuthenticated() {
    return !!this.accessToken;
  }

  async refreshAccessToken() {
    return this.client.post('/api/auth/refresh', { refresh_token: this.refreshToken });
  }

  // Auth
  async login(email: string, password: string) {
    const response = await this.client.post('/api/auth/login', { email, password });
    if (response.data.access_token) {
      this.setTokens(response.data.access_token, response.data.refresh_token);
    }
    return response;
  }

  async register(data: { email: string; password: string; name: string; company_name: string; company_slug: string }) {
    const response = await this.client.post('/api/auth/register', data);
    if (response.data.access_token) {
      this.setTokens(response.data.access_token, response.data.refresh_token);
    }
    return response;
  }

  async getCurrentUser() {
    return this.client.get('/api/auth/me');
  }

  // Companies
  async getCompany() {
    return this.client.get('/api/companies/me');
  }

  async updateCompany(data: any) {
    return this.client.put('/api/companies/me', data);
  }

  async getCompanySettings() {
    return this.client.get('/api/companies/me/settings');
  }

  async updateCompanySettings(data: any) {
    return this.client.put('/api/companies/me/settings', data);
  }

  // Leads
  async getLeads(params?: { page?: number; page_size?: number; search?: string; source?: string; email_status?: string }) {
    return this.client.get('/api/leads', { params });
  }

  async getLead(id: number) {
    return this.client.get(`/api/leads/${id}`);
  }

  async createLead(data: any) {
    return this.client.post('/api/leads', data);
  }

  async updateLead(id: number, data: any) {
    return this.client.put(`/api/leads/${id}`, data);
  }

  async deleteLead(id: number) {
    return this.client.delete(`/api/leads/${id}`);
  }

  async importLeads(leads: any[], source: string) {
    return this.client.post('/api/leads/import', { leads, source });
  }

  async verifyLeadEmail(id: number) {
    return this.client.post(`/api/leads/verify/${id}`);
  }

  async enrichLead(id: number) {
    return this.client.post(`/api/leads/enrich/${id}`);
  }

  async exportLeadsCsv(leadIds?: number[]) {
    return this.client.get('/api/leads/export/csv', { 
      params: { lead_ids: leadIds },
      responseType: 'blob'
    });
  }

  // Campaigns
  async getCampaigns(params?: { page?: number; page_size?: number; status?: string }) {
    return this.client.get('/api/campaigns', { params });
  }

  async getCampaign(id: number) {
    return this.client.get(`/api/campaigns/${id}`);
  }

  async createCampaign(data: any) {
    return this.client.post('/api/campaigns', data);
  }

  async updateCampaign(id: number, data: any) {
    return this.client.put(`/api/campaigns/${id}`, data);
  }

  async deleteCampaign(id: number) {
    return this.client.delete(`/api/campaigns/${id}`);
  }

  async startCampaign(id: number) {
    return this.client.post(`/api/campaigns/${id}/start`);
  }

  async pauseCampaign(id: number) {
    return this.client.post(`/api/campaigns/${id}/pause`);
  }

  async resumeCampaign(id: number) {
    return this.client.post(`/api/campaigns/${id}/resume`);
  }

  async cancelCampaign(id: number) {
    return this.client.post(`/api/campaigns/${id}/cancel`);
  }

  async getCampaignSequences(campaignId: number) {
    return this.client.get(`/api/campaigns/${campaignId}/sequences`);
  }

  async addCampaignSequence(campaignId: number, data: any) {
    return this.client.post(`/api/campaigns/${campaignId}/sequences`, data);
  }

  async updateCampaignSequence(campaignId: number, sequenceId: number, data: any) {
    return this.client.put(`/api/campaigns/${campaignId}/sequences/${sequenceId}`, data);
  }

  async deleteCampaignSequence(campaignId: number, sequenceId: number) {
    return this.client.delete(`/api/campaigns/${campaignId}/sequences/${sequenceId}`);
  }

  async addLeadsToCampaign(campaignId: number, leadIds: number[]) {
    return this.client.post(`/api/campaigns/${campaignId}/leads`, { lead_ids: leadIds });
  }

  // Scraping
  async getScrapingJobs(params?: { page?: number; page_size?: number; status?: string }) {
    return this.client.get('/api/scraping/jobs', { params });
  }

  async getScrapingJob(id: number) {
    return this.client.get(`/api/scraping/jobs/${id}`);
  }

  async createScrapingJob(data: any) {
    return this.client.post('/api/scraping/jobs', data);
  }

  async startScrapingJob(id: number) {
    return this.client.post(`/api/scraping/jobs/${id}/start`);
  }

  async cancelScrapingJob(id: number) {
    return this.client.post(`/api/scraping/jobs/${id}/cancel`);
  }

  async deleteScrapingJob(id: number) {
    return this.client.delete(`/api/scraping/jobs/${id}`);
  }

  async scrapeLinkedIn(data: any) {
    return this.client.post('/api/scraping/linkedin', data);
  }

  async scrapeGoogleMaps(data: any) {
    return this.client.post('/api/scraping/google-maps', data);
  }

  // Analytics
  async getDashboardStats() {
    return this.client.get('/api/analytics/dashboard');
  }

  async getLeadAnalytics() {
    return this.client.get('/api/analytics/leads');
  }

  async getCampaignAnalytics() {
    return this.client.get('/api/analytics/campaigns');
  }

  async getTeamActivity() {
    return this.client.get('/api/analytics/team');
  }
}

export const api = new ApiClient();
export default api;
