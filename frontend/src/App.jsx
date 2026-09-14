import React, { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Play, Pause, Loader, LogOut, User } from 'lucide-react'
import axios from 'axios'
import Auth from './Auth'
import Profile from './Profile'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [response, setResponse] = useState('')
  const [error, setError] = useState('')
  const [audioUrl, setAudioUrl] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [textInput, setTextInput] = useState('')
  const [inputMode, setInputMode] = useState('voice')
  const [language, setLanguage] = useState('en')
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState('')
  const [modalInput, setModalInput] = useState('')
  const [showProfile, setShowProfile] = useState(false)

  const mediaRecorderRef = useRef(null)
  const audioRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const response = await axios.get(`${API_URL}/api/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setUser(response.data)
        setLanguage(response.data.language)
        setIsAuthenticated(true)
      } catch (error) {
        localStorage.removeItem('token')
        setIsAuthenticated(false)
      }
    }
  }

  const handleLogin = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/api/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUser(response.data)
      setLanguage(response.data.language)
      setIsAuthenticated(true)
    } catch (error) {
      localStorage.removeItem('token')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    setUser(null)
    setResponse('')
    setError('')
    setAudioUrl(null)
  }

  const startRecording = async () => {
    try {
      setError('')
      setResponse('')
      setAudioUrl(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      chunksRef.current = []
      mediaRecorderRef.current.ondataavailable = (event) => {
        chunksRef.current.push(event.data)
      }
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' })
        await processAudio(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }
      mediaRecorderRef.current.start()
      setIsRecording(true)
    } catch (err) {
      setError('Microphone access denied. Please allow microphone access and try again.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const processAudio = async (audioBlob) => {
    setIsProcessing(true)
    setError('')
    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', audioBlob)
      formData.append('language', language)
      const response = await axios.post(`${API_URL}/process-audio`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
      })
      setResponse({
        transcript: response.data.transcript,
        response_text: response.data.response_text
      })
      if (response.data.audio_data) {
        const audioBlob = new Blob([Uint8Array.from(atob(response.data.audio_data), c => c.charCodeAt(0))], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)
        setAudioUrl(audioUrl)
        // Auto-play audio after setting URL
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.play()
            setIsPlaying(true)
          }
        }, 100)
      }
    } catch (err) {
      setError('Failed to process audio')
      console.error(err)
    } finally {
      setIsProcessing(false)
    }
  }

  const processText = async () => {
    if (!textInput.trim()) {
      setError('Please enter some text to process.')
      return
    }
    setIsProcessing(true)
    setError('')
    setResponse('')
    setAudioUrl(null)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/process-text`, {
        text: textInput.trim(),
        language
      }, {
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      })
      setResponse({
        transcript: textInput,
        response_text: response.data.response_text || response.data
      })
      if (response.data.audio_data) {
        const audioBlob = new Blob([Uint8Array.from(atob(response.data.audio_data), c => c.charCodeAt(0))], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)
        setAudioUrl(audioUrl)
        // Auto-play audio after setting URL
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.play()
            setIsPlaying(true)
          }
        }, 100)
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to process text. Please try again.'
      setError(errorMessage)
      console.error('Error processing text:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const playAudio = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
        setIsPlaying(false)
      } else {
        audioRef.current.play()
        setIsPlaying(true)
      }
    }
  }

  const handleAudioEnded = () => setIsPlaying(false)

  // -------------------- Modal Handlers --------------------
  const openModal = (type) => {
    setModalType(type)
    // Pre-fill user's city for weather
    if (type === 'weather' && user?.location) {
      const city = user.location.split(',')[0].trim() // Extract city from "Markapur, Andhra Pradesh"
      setModalInput(city)
    } else {
      setModalInput('')
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setModalInput('')
  }

  const handleModalSubmit = async () => {
    if (!modalInput.trim()) return
    setShowModal(false)
    setIsProcessing(true)
    
    try {
      const token = localStorage.getItem('token')
      let res
      if (modalType === 'weather') {
        res = await axios.post(`${API_URL}/api/weather`, { city: modalInput, language }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      } else if (modalType === 'crop') {
        res = await axios.post(`${API_URL}/api/crop-prices`, { crop: modalInput, language }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      } else if (modalType === 'schemes') {
        res = await axios.post(`${API_URL}/api/gov-schemes`, { topic: modalInput, language }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      }
      setResponse({ transcript: modalInput, response_text: res.data.text })
      if (res.data.audio_data) {
        const audioBlob = new Blob([Uint8Array.from(atob(res.data.audio_data), c => c.charCodeAt(0))], { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)
        setAudioUrl(audioUrl)
        // Auto-play audio after setting URL
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.play()
            setIsPlaying(true)
          }
        }, 100)
      }
    } catch {
      setError(`Unable to fetch ${modalType} information.`)
    } finally {
      setIsProcessing(false)
      setModalInput('')
    }
  }

  if (!isAuthenticated) {
    return <Auth onLogin={handleLogin} />
  }

  if (showProfile) {
    return (
      <Profile 
        user={user} 
        onBack={() => setShowProfile(false)}
        onUserUpdate={(updatedUser) => setUser({...user, ...updatedUser})}
      />
    )
  }

  return (
    <div className="container">
      <div className="header">
        <div className="logo">
          <div className="logo-icon">🌾</div>
          <div className="logo-text">
            <h1>Gram Vaani</h1>
            <p>AI Voice Assistant for Rural India</p>
          </div>
          <div className="user-info">
            <div className="user-details">
              <span className="user-email">{user?.email}</span>
              <span className="user-location">📍 {user?.location}</span>
            </div>
            <div className="user-actions">
              <button onClick={() => setShowProfile(true)} className="profile-btn">
                <User size={20} />
              </button>
              <button onClick={handleLogout} className="logout-btn">
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="main-card">
        <div className="input-mode-selector">
          <button className={`mode-button ${inputMode === 'voice' ? 'active' : ''}`} onClick={() => setInputMode('voice')}>🎤 Voice</button>
          <button className={`mode-button ${inputMode === 'text' ? 'active' : ''}`} onClick={() => setInputMode('text')}>✍ Text</button>
        </div>

        {inputMode === 'voice' ? (
          <div className="voice-section">
            <button className={`voice-button ${isRecording ? 'recording' : ''}`} onClick={isRecording ? stopRecording : startRecording} disabled={isProcessing}>
              {isProcessing ? <Loader className="loading" /> : isRecording ? <MicOff size={40} /> : <Mic size={40} />}
            </button>
            <div className="status-text">
              {isRecording ? "🎤 Listening... Click to stop" :
                isProcessing ? "🤖 Processing your request..." :
                  "👆 Click to speak in your local dialect"}
            </div>
            <div className="language-selector-inline">
              <div className="language-icon">🌐</div>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">🇺🇸 English</option>
                <option value="hi">🇮🇳 Hindi</option>
                <option value="mr">🇮🇳 Marathi</option>
                <option value="bn">🇮🇳 Bengali</option>
                <option value="ta">🇮🇳 Tamil</option>
                <option value="te">🇮🇳 Telugu</option>
              </select>
            </div>
          </div>
        ) : (
          <div className="text-section">
            <textarea value={textInput} onChange={(e) => setTextInput(e.target.value)} placeholder="Type your question here..." className="text-input" rows={3} disabled={isProcessing} />
            <div className="text-controls">
              <button className="submit-button" onClick={processText} disabled={isProcessing || !textInput.trim()}>
                {isProcessing ? <><Loader className="loading" size={16} /> Processing...</> : 'Submit Question'}
              </button>
              <div className="language-selector-inline">
                <div className="language-icon">🌐</div>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                  <option value="en">🇺🇸 English</option>
                  <option value="hi">🇮🇳 Hindi</option>
                  <option value="mr">🇮🇳 Marathi</option>
                  <option value="bn">🇮🇳 Bengali</option>
                  <option value="ta">🇮🇳 Tamil</option>
                  <option value="te">🇮🇳 Telugu</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Feature buttons */}
        <div className="feature-buttons">
          <button className="feature-card" onClick={() => openModal('weather')}>
            <div className="icon">🌤</div>
            <div className="title">Check Weather</div>
            <div className="description">Get real-time weather updates for your area.</div>
          </button>
          <button className="feature-card" onClick={() => openModal('crop')}>
            <div className="icon">💰</div>
            <div className="title">Crop Prices</div>
            <div className="description">Get the latest market prices for your crops.</div>
          </button>
          <button className="feature-card" onClick={() => openModal('schemes')}>
            <div className="icon">🏛</div>
            <div className="title">Govt Schemes</div>
            <div className="description">Learn about government schemes available to you.</div>
          </button>
          {/* <button className="feature-card">
            <div className="icon">🗣</div>
            <div className="title">Multi-Dialect Support</div>
            <div className="description">Speak in your local language – Hindi, Telugu, Punjabi, Bhojpuri, and more.</div>
          </button> */}
        </div>

        {error && <div className="error-message">{error}</div>}

        {response && (
          <div className="response-section">
            <h3>📝 What you said:</h3>
            <p className="response-text">{response.transcript}</p>
            <h3>💬 Response:</h3>
            <p className="response-text">{response.response_text}</p>
            {audioUrl && (
              <div className="audio-controls">
                <button className="play-button" onClick={playAudio}>
                  {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                  {isPlaying ? 'Pause' : 'Play Response'}
                </button>
                <audio ref={audioRef} src={audioUrl} onEnded={handleAudioEnded} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {modalType === 'weather' && '🌤 Weather Information'}
                {modalType === 'crop' && '💰 Crop Prices'}
                {modalType === 'schemes' && '🏛 Government Schemes'}
              </h3>
              <button className="close-button" onClick={closeModal}>×</button>
            </div>
            <div className="modal-body">
              <label>
                {modalType === 'weather' && 'Enter your city:'}
                {modalType === 'crop' && 'Enter crop name:'}
                {modalType === 'schemes' && 'Enter topic (e.g., irrigation, fertilizer):'}
              </label>
              <input
                type="text"
                value={modalInput}
                onChange={(e) => setModalInput(e.target.value)}
                placeholder={
                  modalType === 'weather' ? 'e.g., Delhi, Mumbai' :
                  modalType === 'crop' ? 'e.g., Rice, Wheat' :
                  'e.g., Irrigation, Seeds'
                }
                onKeyPress={(e) => e.key === 'Enter' && handleModalSubmit()}
                autoFocus
              />
            </div>
            <div className="modal-footer">
              <button className="cancel-button" onClick={closeModal}>Cancel</button>
              <button className="submit-button" onClick={handleModalSubmit} disabled={!modalInput.trim()}>Get Information</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
