const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${API_BASE}/api`;

const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  const res = await fetch(`${API}/${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
  return res.json();
};

export const login = (email, pass) => apiCall('login', {
  method: 'POST',
  body: JSON.stringify({ username: email, password: pass }),
});

export const getMe = () => apiCall('me');

export const updateSetting = (key, value) => apiCall('settings', {
  method: 'PUT',
  body: JSON.stringify({ [key]: value }),
});

export const updateSettings = (settings) => apiCall('settings', {
  method: 'PUT',
  body: JSON.stringify(settings),
});

export const getSettings = () => apiCall('settings');