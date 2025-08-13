import axios from 'axios';

// backend API 
const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// make the call the API
export const chatService = {
  sendMessage: async (question) => {
    try {
      const response = await apiClient.post('/chat', {
        user_id: 'user1', // hardcoded now
        question: question,
        session_id: 'default' // hardcoded now
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  submitApproval: async (decision, feedbackMessage = '') => {
    try {
      const response = await apiClient.post('/human-approval', {
        user_id: 'user1', // hardcoded now
        session_id: 'default', // hardcoded now
        decision: decision,
        feedback_message: feedbackMessage
      });
      return response.data;
    } catch (error) {
      console.error('Error submitting approval:', error);
      throw error;
    }
  },

};