# Frontend Integration Guide

This document explains how to integrate the Campaign OS backend with the React frontend application.

## 🔗 Connection Setup

### 1. Environment Configuration

In the React frontend (`.env` or `.env.local`):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=30000
VITE_WS_URL=ws://localhost:8000/ws
```

### 2. API Client Setup

Create a utility file for API calls:

```typescript
// src/utils/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Add JWT token to headers
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        localStorage.setItem('access_token', data.access);
        return apiClient(error.config);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

## 📲 Frontend Data Model Mapping

### Masters Data

```typescript
// Directory/Area → District/Constituency
interface Area {
  id: string;
  key: string;        // District/Constituency code
  meta: string;       // "State Name · Total Booths"
}

// Booth Entry
interface BoothRecord {
  id: string;
  keyField: string;   // "Booth 001 – School XYZ"
  sub: string;        // "Modakkurichi · 885 voters · Agent: Raj Kumar"
  data: {
    num: string;      // Booth number
    name: string;     // Booth name/location
    area: string;     // Area code
    village: string;  // Ward name
    address: string;  // Full address
    voters: number;   // Total voters count
    male: number;     // Male voters
    female: number;   // Female voters
    agent: string;    // Primary agent name
    agentph: string;  // Agent phone
    status: string;   // Booth status
    sentiment: string;// Booth sentiment
    notes: string;    // Additional notes
  };
  createdAt: string;  // ISO timestamp
}
```

### Voter Entry

```typescript
interface VoterRecord {
  id: string;
  keyField: string;   // "{voter_name} – {voter_id}"
  sub: string;        // "{booth_name} · {phone} · {sentiment}"
  data: {
    id: string;       // Voter ID
    name: string;     // Full name
    phone: string;    // Phone number
    booth: string;    // Booth assignment
    gender: string;   // Gender
    sentiment: string;// voter_sentiment
    address: string;  // Home address
  };
  createdAt: string;
}
```

## 🔐 Authentication Flow

### 1. Login

```typescript
// src/hooks/useAuth.ts
import { useState } from 'react';
import apiClient from '@/utils/api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const { data } = await apiClient.post('/auth/login/', {
        username,
        password,
      });
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // Get user info
      const userResponse = await apiClient.get('/auth/users/me/');
      setUser(userResponse.data);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return { user, login, logout, loading };
}
```

### 2. Protected Routes

```typescript
// src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import apiClient from '@/utils/api';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      apiClient
        .get('/auth/users/me/')
        .then(() => setIsAuthenticated(true))
        .catch(() => {
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
        })
        .finally(() => setLoading(false));
    } else {
      setIsAuthenticated(false);
      setLoading(false);
    }
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;
  return <>{children}</>;
}
```

## 📡 Data Fetching Examples

### Get Booths

```typescript
// src/hooks/useBooths.ts
import { useState, useEffect } from 'react';
import apiClient from '@/utils/api';

export function useBooths(constituency_id: number) {
  const [booths, setBooths] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get('/masters/booths/', {
        params: { ward__constituency: constituency_id },
      })
      .then((response) => {
        // Transform API response to frontend format
        const transformed = response.data.results.map((booth) => ({
          id: booth.id.toString(),
          keyField: `Booth ${booth.number} – ${booth.name}`,
          sub: `${booth.ward_name} · ${booth.total_voters} voters · Agent: ${booth.agent_name || 'Not assigned'}`,
          data: {
            num: booth.number,
            name: booth.name,
            area: booth.ward_name,
            voters: booth.total_voters,
            agent: booth.agent_name || '',
            status: booth.status,
            sentiment: booth.sentiment,
          },
          createdAt: booth.created_at,
        }));
        setBooths(transformed);
      })
      .finally(() => setLoading(false));
  }, [constituency_id]);

  return { booths, loading };
}
```

### Get Voters

```typescript
// src/hooks/useVoters.ts
export function useVoters(booth_id: number) {
  const [voters, setVoters] = useState([]);

  useEffect(() => {
    apiClient
      .get('/voters/voters/', {
        params: { booth: booth_id },
      })
      .then((response) => {
        const transformed = response.data.results.map((voter) => ({
          id: voter.id.toString(),
          keyField: `${voter.name} – ${voter.voter_id}`,
          sub: `${voter.booth_name} · ${voter.phone} · ${voter.sentiment}`,
          data: {
            id: voter.voter_id,
            name: voter.name,
            phone: voter.phone,
            booth: voter.booth,
            sentiment: voter.sentiment,
          },
          createdAt: voter.created_at,
        }));
        setVoters(transformed);
      });
  }, [booth_id]);

  return { voters };
}
```

### Create Voter

```typescript
async function createVoter(voterData) {
  const payload = {
    name: voterData.data.name,
    voter_id: voterData.data.id,
    phone: voterData.data.phone,
    booth: voterData.data.booth,
    ward: voterData.booth.ward_id, // From booth context
    address: voterData.data.address || '',
    gender: voterData.data.gender || 'm',
    sentiment: voterData.data.sentiment || 'undecided',
  };

  const response = await apiClient.post('/voters/voters/', payload);
  return response.data;
}
```

## 📊 Analytics Integration

### Dashboard Stats

```typescript
// src/hooks/useDashboard.ts
export function useDashboard(constituency_id?: number) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = constituency_id ? { constituency_id } : {};
    apiClient
      .get('/analytics/dashboard/', { params })
      .then((response) => setStats(response.data))
      .finally(() => setLoading(false));
  }, [constituency_id]);

  return { stats, loading };
}
```

### Usage in Component

```typescript
// src/pages/DashboardPage.tsx
export default function DashboardPage() {
  const { stats, loading } = useDashboard();

  if (loading) return <Spinner />;

  return (
    <>
      <StatCard
        label="Electorate"
        value={stats.total_voters.toLocaleString()}
        sub="Registered voters"
      />
      <StatCard
        label="Coverage"
        value={`${Math.round((stats.voters_contacted / stats.total_voters) * 100)}%`}
        sub={`${stats.voters_contacted} contacted`}
        progress={(stats.voters_contacted / stats.total_voters) * 100}
      />
    </>
  );
}
```

## 🔄 CRUD Operations

### Create

```typescript
async function addBooth(booth) {
  const response = await apiClient.post('/masters/booths/', {
    number: booth.data.num,
    name: booth.data.name,
    ward: booth.ward_id,
    code: booth.data.num,
    address: booth.data.address,
    total_voters: parseInt(booth.data.voters),
    status: booth.data.status,
  });
  return response.data;
}
```

### Update

```typescript
async function updateBooth(boothId, booth) {
  const response = await apiClient.patch(`/masters/booths/${boothId}/`, {
    status: booth.data.status,
    sentiment: booth.data.sentiment,
    primary_agent: booth.agent_id,
  });
  return response.data;
}
```

### Delete

```typescript
async function deleteBooth(boothId) {
  await apiClient.delete(`/masters/booths/${boothId}/`);
}
```

## 📛 Filtering & Search

```typescript
// Get filtered data
async function searchVoters(query: string, booth_id: number) {
  const response = await apiClient.get('/voters/voters/', {
    params: {
      booth: booth_id,
      search: query, // Searches name, voter_id, phone
      limit: 50,
      offset: 0,
    },
  });
  return response.data;
}

// Sentiment filter
async function getVotersBySentiment(sentiment: string) {
  const response = await apiClient.get('/voters/voters/', {
    params: { sentiment },
  });
  return response.data;
}

// Contact status
async function getUncontactedVoters() {
  const response = await apiClient.get('/voters/voters/uncontacted/');
  return response.data;
}
```

## 🎯 Common Patterns

### Pagination in React Hook

```typescript
interface UseListOptions {
  page: number;
  pageSize: number;
  filters?: Record<string, any>;
  search?: string;
}

export function useList(endpoint: string, options: UseListOptions) {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiClient
      .get(endpoint, {
        params: {
          limit: options.pageSize,
          offset: (options.page - 1) * options.pageSize,
          search: options.search,
          ...options.filters,
        },
      })
      .then((response) => {
        setData(response.data.results);
        setTotal(response.data.count);
      })
      .finally(() => setLoading(false));
  }, [endpoint, options.page, options.pageSize]);

  return { data, total, loading, pages: Math.ceil(total / options.pageSize) };
}
```

## 🚨 Error Handling

```typescript
import { useToast } from './useToast';

export function useApi() {
  const { showError, showSuccess } = useToast();

  const request = async (promise: Promise<any>) => {
    try {
      const response = await promise;
      showSuccess('Operation successful');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.detail || 'An error occurred';
      showError(message);
      throw error;
    }
  };

  return { request };
}
```

## 📱 Real-time Updates (WebSocket)

Future enhancement for live updates:

```typescript
// Not yet implemented - planned for v0.2.0
// Examples:
// - Live booth sentiment updates
// - Live volunteer location tracking
// - Live event attendance count
// - Real-time notification feed
```

## ✅ Complete Integration Checklist

- [ ] Setup API client with axios
- [ ] Configure environment variables
- [ ] Implement JWT authentication
- [ ] Setup protected routes
- [ ] Create custom hooks for data fetching
- [ ] Implement data transformation layer
- [ ] Add error handling and loading states
- [ ] Setup pagination
- [ ] Implement search/filter
- [ ] Add offline support (optional)
- [ ] Setup caching (optional)
- [ ] Configure WebSocket (future)

## 📞 Support & Debugging

### Check API Status

```bash
# From React console
fetch('http://localhost:8000/api/v1/auth/users/me/', {
  headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
})
  .then(r => r.json())
  .then(console.log);
```

### CORS Issues

If you see CORS errors:
1. Verify CORS_ALLOWED_ORIGINS in backend .env
2. Include frontend origin: `http://localhost:5173`
3. Restart Django server

### Token Issues

If token is invalid:
1. Clear localStorage: `localStorage.clear()`
2. Login again
3. Check token expiration (24 hours)

---

**Happy Coding! 🚀**
