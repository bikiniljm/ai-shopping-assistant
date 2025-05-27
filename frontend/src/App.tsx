import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import type { ChatMessage, ChatResponse, ChatRequest } from './types/chat'
import { ChatMessage as ChatMessageComponent } from './components/ChatMessage'
import { FaPlus, FaArrowRight } from 'react-icons/fa'
import { RiRobot2Fill } from 'react-icons/ri'
import './App.css'

const API_URL = 'https://d11n1w3ly1tcs5.cloudfront.net';

function generateSessionId() {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([{
    text: "I'm your AI shopping assistant! You can answer questions or upload a product photo you're looking for!\n\nYou might ask me:\n• Find me comfortable running shoes for women\n• What are some good toys for a 4-year-old?\n• I need a new laptop for video editing\n",
    timestamp: new Date().toISOString(),
    isUser: false
  }])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(generateSessionId())
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleNewChat = () => {
    setMessages([{
      text: "I'm your AI shopping assistant! You can answer questions or upload a product photo you're looking for!\n\nYou might ask me:\n• Find me comfortable running shoes for women\n• What are some good toys for a 4-year-old?\n• I need a new laptop for video editing\n",
      timestamp: new Date().toISOString(),
      isUser: false
    }])
    setInputText('')
    setIsLoading(false)
    setSessionId(generateSessionId())
  }

  const handleExampleClick = (question: string) => {
    setInputText(question.replace(/[""]/g, ''))
  }

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim()) return

    const userMessage: ChatMessage = {
      text: inputText,
      timestamp: new Date().toISOString(),
      isUser: true
    }
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      const chatRequest: ChatRequest = {
        text: inputText,
        sessionId: sessionId
      }
      
      const response = await axios.post<ChatResponse>(`${API_URL}/api/chat/text/v2`, chatRequest)
      
      console.log('API Response:', response.data)

      if (!response.data) {
        throw new Error('Empty response from server')
      }

      const botMessage: ChatMessage = {
        text: response.data.text || 'I understand what you\'re looking for, but I need a bit more information to help you better. Could you provide more details about your preferences?',
        timestamp: response.data.timestamp || new Date().toISOString(),
        isUser: false,
        products: Array.isArray(response.data.products) ? response.data.products : [],
        search_params: response.data.search_params || undefined
      }
      setMessages(prev => [...prev, botMessage])
      scrollToBottom()
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        text: 'I\'m having a bit of trouble connecting to our product database right now. Could you try asking your question again in a moment? I\'m here to help!',
        timestamp: new Date().toISOString(),
        isUser: false
      }
      setMessages(prev => [...prev, errorMessage])
      scrollToBottom()
    } finally {
      setIsLoading(false)
    }
  }

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const imageUrl = URL.createObjectURL(file)

    const userMessage: ChatMessage = {
      text: "Uploaded an image",
      timestamp: new Date().toISOString(),
      isUser: true,
      user_message: {
        type: 'image',
        content: imageUrl
      }
    }
    setMessages(prev => [...prev, userMessage])
    scrollToBottom()

    setIsLoading(true)

    const formData = new FormData()
    formData.append('image', file)
    formData.append('sessionId', sessionId)

    try {
      const response = await axios.post<ChatResponse>(`${API_URL}/api/chat/image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const botMessage: ChatMessage = {
        text: response.data.text,
        timestamp: response.data.timestamp,
        isUser: false,
        products: response.data.products,
        search_params: response.data.search_params
      }
      setMessages(prev => [...prev, botMessage])
      scrollToBottom()
    } catch (error) {
      console.error('Error uploading image:', error)
      const errorMessage: ChatMessage = {
        text: "I apologize, but I encountered an error while analyzing the image. Could you please try uploading it again or describe what you're looking for?",
        timestamp: new Date().toISOString(),
        isUser: false
      }
      setMessages(prev => [...prev, errorMessage])
      scrollToBottom()
    } finally {
      setIsLoading(false)
      URL.revokeObjectURL(imageUrl)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="app-container">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <h1>AI Shopping Assistant</h1>
          </div>
          <button 
            className="new-chat-button"
            onClick={handleNewChat}
            disabled={isLoading}
          >
            New Chat
          </button>
        </div>
        
        <div className="chat-messages">
          {messages.map((message, index) => (
            <ChatMessageComponent 
              key={index} 
              message={message} 
              onExampleClick={(text) => {
                setInputText(text);
                const input = document.querySelector('.text-input') as HTMLInputElement;
                if (input) {
                  input.focus();
                }
              }}
            />
          ))}
          {isLoading && (
            <div className="chat-message">
              <div className="message-avatar">
                <RiRobot2Fill size={24} />
              </div>
              <div className="message-content" style={{ backgroundColor: 'white', padding: '1rem', borderRadius: '8px' }}>
                <div className="message-text" style={{ backgroundColor: '#f8f9fa', padding: '1rem', borderRadius: '8px' }}>
                  Thinking...
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <form onSubmit={handleTextSubmit} className="input-form">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask about products..."
              className="text-input"
              disabled={isLoading}
            />
            <button 
              type="button" 
              className="upload-button button-tooltip" 
              onClick={() => fileInputRef.current?.click()} 
              disabled={isLoading}
              data-tooltip="Upload an image"
            >
              <FaPlus size={20} />
            </button>
            <button 
              type="submit" 
              className="send-button button-tooltip" 
              disabled={isLoading}
              data-tooltip="Send"
            >
              <FaArrowRight size={20} />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
              disabled={isLoading}
            />
          </form>
        </div>
      </div>
    </div>
  )
}

export default App
