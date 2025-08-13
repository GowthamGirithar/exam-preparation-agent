import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatService } from './apiService';

// included in app.jsx
const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [approvalFeedback, setApprovalFeedback] = useState('');

  // Handle approval decision
  const handleApproval = async (decision) => {
    if (!pendingApproval) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await chatService.submitApproval(decision, approvalFeedback);
      
      // Add approval decision message
      const decisionMessage = {
        id: Date.now(),
        text: `✅ Decision: ${decision.toUpperCase()} - ${approvalFeedback ? `\n\nFeedback: ${approvalFeedback}` : ''}`,
        sender: 'user',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, decisionMessage]);
      
      // Add the final response from the resumed workflow
      if (response.response) {
        const botMessage = {
          id: Date.now() + 1,
          text: response.response,
          sender: 'bot',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, botMessage]);
      }
      
      // Clear approval state
      setPendingApproval(null);
      setApprovalFeedback('');
      
    } catch (err) {
      setError('Failed to submit approval decision. Please try again.');
      console.error('Approval error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.sendMessage(inputValue);
      
      // Check if approval is needed
      if (response.needs_approval) {
        setPendingApproval(response);
        // Don't add a chat message - the approval interface will show all details
      } else {
        // Normal response
        const botMessage = {
          id: Date.now() + 1,
          text: response.response,
          sender: 'bot',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, botMessage]);
      }
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-blue-600 text-white p-3 shadow-md flex-shrink-0">
        <h1 className="text-xl font-semibold">Personal Law Exam Coaching Assistant</h1>
        <p className="text-blue-100 text-sm">You can practise questions related to grammer and other topics and also track perfromance metrics. </p>
      </div>

      {/* Messages Container */}
      <div className="overflow-y-auto p-4 space-y-4 grow">
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-800 shadow-md'
              }`}
            >
              {message.sender === 'bot' ? (
                <ReactMarkdown className="text-sm prose prose-sm max-w-none">
                  {message.text}
                </ReactMarkdown>
              ) : (
                <p className="text-sm">{message.text}</p>
              )}
              <p className={`text-xs mt-1 ${
                message.sender === 'user' ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 shadow-md max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <p className="text-sm">{pendingApproval ? 'Processing approval...' : 'Thinking...'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Human Approval Interface */}
        {pendingApproval && !isLoading && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-yellow-400 rounded-lg p-6 mx-2 shadow-lg">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">⚠️</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-yellow-800 mb-3">🤖 Human Approval Required</h3>
                
                {/* Approval Details */}
                <div className="bg-white rounded-lg p-4 mb-4 shadow-sm">
                  <div className="grid grid-cols-1 gap-3 text-sm">
                    <div className="flex items-center">
                      <span className="font-semibold text-gray-700 w-20">Confidence:</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-red-500 h-2 rounded-full"
                            style={{width: `${pendingApproval.confidence_score * 100}%`}}
                          ></div>
                        </div>
                        <span className="text-red-600 font-medium">{(pendingApproval.confidence_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    
                    <div>
                      <span className="font-semibold text-gray-700">Plan:</span>
                      <p className="text-gray-600 mt-1">{pendingApproval.plan_reasoning}</p>
                    </div>
                    
                    {pendingApproval.tools_to_use && pendingApproval.tools_to_use.length > 0 && (
                      <div>
                        <span className="font-semibold text-gray-700">Tools to execute:</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {pendingApproval.tools_to_use.map((tool, index) => (
                            <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                              {tool.tool_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Optional feedback input */}
                <div className="mb-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    💬 Optional feedback or modifications:
                  </label>
                  <textarea
                    value={approvalFeedback}
                    onChange={(e) => setApprovalFeedback(e.target.value)}
                    placeholder="Add any feedback, modifications, or special instructions..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    rows="3"
                  />
                </div>
                
                {/* Approval buttons */}
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => handleApproval('approve')}
                    className="flex items-center space-x-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors font-medium"
                  >
                    <span>✅</span>
                    <span>Approve & Continue</span>
                  </button>
                  <button
                    onClick={() => handleApproval('reject')}
                    className="flex items-center space-x-2 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors font-medium"
                  >
                    <span>❌</span>
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleApproval('modify')}
                    className="flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors font-medium"
                  >
                    <span>🔄</span>
                    <span>Request Changes</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Form - Fixed at bottom */}
      <div className="bg-white border-t border-gray-200 p-4 sticky bottom-0 z-10">
        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 mb-3 rounded">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="flex space-x-10">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={pendingApproval ? "Please respond to the approval request above..." : "Ask a law question..."}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading || pendingApproval}
            autoFocus={!pendingApproval}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim() || pendingApproval}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isLoading ? 'Sending...' : 'SEND'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;