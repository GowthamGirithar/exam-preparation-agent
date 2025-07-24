# Law Exam Agent - Frontend

A simple React.js frontend application that provides a chat interface for interacting with the Law Exam Agent backend.

## Features

- 💬 **Clean Chat Interface**: Modern chat UI with message bubbles
- 🔄 **Real-time Communication**: Connects to FastAPI backend via REST API
- ⚡ **Loading States**: Visual feedback during API calls
- 🎨 **Responsive Design**: Works on desktop, tablet, and mobile
- 🚨 **Error Handling**: User-friendly error messages
- 📚 **Law Exam Support**: Integrated with InteractiveLearningAgent

## Tech Stack

- **React 19** - Frontend framework
- **Vite 5** - Build tool and development server
- **Tailwind CSS 4** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **JavaScript (ES6+)** - Programming language

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn package manager
- Law Exam Agent backend running on `http://localhost:8000`

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd law-exam-agent/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser** and navigate to:
   ```
   http://localhost:5173
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/
│   │   └── ChatInterface.jsx    # Main chat component
│   ├── services/
│   │   └── apiService.js        # Backend API communication
│   ├── App.jsx                  # Main app component
│   ├── index.css               # Global styles with Tailwind
│   └── main.jsx                # App entry point
├── index.html                  # HTML template
├── package.json               # Dependencies and scripts
├── tailwind.config.js         # Tailwind CSS configuration
├── postcss.config.js          # PostCSS configuration
└── vite.config.js             # Vite configuration
```

## API Integration

The frontend communicates with the backend using the following endpoint:

- **POST** `/chat` - Send questions to the law exam agent
  ```json
  {
    "user_id": "user1",
    "question": "What is contract law?",
    "session_id": "default"
  }
  ```

## Configuration

### Backend URL
The API base URL is configured in `src/apiService.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Default Values
- **User ID**: `user1`
- **Session ID**: `default`

## Usage

1. **Start the backend server** (Law Exam Agent)
2. **Start the frontend development server**
3. **Open the chat interface** in your browser
4. **Ask law-related questions** such as:
   - "What is contract law?"
   - "Explain tort law"
   - "start practice constitutional law"
   - "my progress"

## Supported Commands

The frontend supports all backend commands including:
- General law questions
- Practice mode: `start practice [topic]`
- Answer submission: `answer A/B/C/D`
- Progress tracking: `my progress`
- Topic explanations: `explain [topic]`
- Session management: `end session`

## Styling

The application uses Tailwind CSS for styling with a modern, clean design:
- **Blue theme** for primary actions
- **Responsive layout** that adapts to screen size
- **Message bubbles** for clear conversation flow
- **Loading animations** for better UX

## Development

### Adding New Features
1. Create new components in `src/components/`
2. Add API methods to `src/apiService.js`
3. Update the main `ChatInterface.jsx` component

### Customizing Styles
- Modify `tailwind.config.js` for theme customization
- Update `src/index.css` for global styles
- Use Tailwind utility classes in components

## Troubleshooting

### Common Issues

1. **Backend Connection Error**:
   - Ensure backend is running on `http://localhost:8000`
   - Check CORS configuration in backend

2. **Styling Issues**:
   - Verify Tailwind CSS is properly configured
   - Check PostCSS configuration

3. **Build Errors**:
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

## License

This project is part of the Law Exam Agent system.
