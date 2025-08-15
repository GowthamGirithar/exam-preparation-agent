# Law Exam Agent - Makefile
# This Makefile provides commands to install dependencies and start servers

.PHONY: help install install-backend install-frontend start-backend start-frontend start dev stop clean setup

# Default target
help:
	@echo "Law Exam Agent - Available Commands:"
	@echo ""
	@echo "Setup (first time):"
	@echo "  make setup            - Complete setup for new developers (install + ready to run)"
	@echo "  make install          - Install dependencies for both backend and frontend"
	@echo "  make install-backend  - Install Python dependencies for backend"
	@echo "  make install-frontend - Install Node.js dependencies for frontend"
	@echo ""
	@echo "Running servers:"
	@echo "  make start            - Start both backend and frontend servers"
	@echo "  make dev              - Start both servers in development mode (alias for start)"
	@echo "  make start-backend    - Start only the backend server"
	@echo "  make start-frontend   - Start only the frontend server"
	@echo ""
	@echo "Maintenance:"
	@echo "  make stop             - Stop all running servers"
	@echo "  make clean            - Clean build artifacts and dependencies"
	@echo ""
	@echo "Backend will run on: http://localhost:8000"
	@echo "Frontend will run on: http://localhost:5173"

# Complete setup for new developers
setup: install
	@echo ""
	@echo "✅ Setup complete! You can now run:"
	@echo "  make start    - to start both servers"
	@echo "  make dev      - same as 'make start'"
	@echo ""

# Install all dependencies
install: install-backend install-frontend
	@echo "✅ All dependencies installed successfully!"

# Install backend dependencies (with virtual environment)
install-backend:
	@echo "📦 Setting up backend virtual environment and installing dependencies..."
	cd backend && python -m venv venv
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Backend virtual environment created and dependencies installed!"
	@echo "💡 Remember to activate the virtual environment: cd backend && source venv/bin/activate"

# Install frontend dependencies
install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed!"

# Start both servers concurrently
start:
	@echo "🚀 Starting Law Exam Agent servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@make -j2 start-backend start-frontend

# Alias for start
dev: start

# Start backend server only
start-backend:
	@echo "🐍 Starting backend server on http://localhost:8000..."
	cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend server only
start-frontend:
	@echo "⚛️  Starting frontend server on http://localhost:5173..."
	cd frontend && npm run dev

# Stop all servers (kills processes on the default ports)
stop:
	@echo "🛑 Stopping servers..."
	-pkill -f "uvicorn main:app"
	-pkill -f "vite"
	@echo "✅ Servers stopped."

# Clean build artifacts and dependencies
clean:
	@echo "🧹 Cleaning build artifacts..."
	cd frontend && rm -rf node_modules dist
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean complete."