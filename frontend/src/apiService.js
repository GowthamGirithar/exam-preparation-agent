import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatService = {
  sendMessage: async (question) => {
    try {
      const response = await apiClient.post('/chat', {
        user_id: 'user1',
        question: question,
        session_id: 'default'
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }
};