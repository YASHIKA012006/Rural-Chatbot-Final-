let currentLanguage = 'hi'; // Default Hindi
let isRecording = false;
let recognition;
let uploadedFile = null;

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('userInput').value = transcript;
        isRecording = false;
        document.getElementById('voiceBtn').classList.remove('recording');
    };
    
    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        document.getElementById('voiceBtn').classList.remove('recording');
        alert('Voice recognition error. Please try again.');
    };
}

// Toggle Language
function toggleLanguage() {
    currentLanguage = currentLanguage === 'hi' ? 'en' : 'hi';
    const langText = document.getElementById('langText');
    langText.textContent = currentLanguage === 'hi' ? 'हिं' : 'EN';
    
    // Update placeholders
    const welcomeText = document.getElementById('welcomeText');
    const welcomeSubtext = document.getElementById('welcomeSubtext');
    
    if (currentLanguage === 'hi') {
        welcomeText.textContent = 'नमस्ते! मैं आपकी मदद के लिए यहाँ हूँ। 🙏';
        welcomeSubtext.textContent = 'कृपया अपना सवाल पूछें या मुझसे बात करें।';
        document.getElementById('userInput').placeholder = 'अपना संदेश यहाँ लिखें...';
    } else {
        welcomeText.textContent = 'Hello! I am here to help you. 🙏';
        welcomeSubtext.textContent = 'Please ask your question or talk to me.';
        document.getElementById('userInput').placeholder = 'Type your message here...';
    }
    
    if (recognition) {
        recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
    }
}

// Toggle Voice
function toggleVoice() {
    if (!recognition) {
        alert('Voice recognition not supported in this browser.');
        return;
    }
    
    if (!isRecording) {
        recognition.start();
        isRecording = true;
        document.getElementById('voiceBtn').classList.add('recording');
    } else {
        recognition.stop();
        isRecording = false;
        document.getElementById('voiceBtn').classList.remove('recording');
    }
}

// Toggle Profile
function toggleProfile() {
    const sidebar = document.getElementById('profileSidebar');
    sidebar.classList.toggle('active');
    
    if (sidebar.classList.contains('active')) {
        loadProfile();
    }
}

// Load Profile
async function loadProfile() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('profileName').value = data.profile.name;
            document.getElementById('profileEmail').textContent = data.profile.email;
        }
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

// Update Profile
async function updateProfile() {
    const name = document.getElementById('profileName').value;
    
    try {
        const response = await fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });
        
        const data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error('Error updating profile:', error);
    }
}

// Upload File
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadedFile = data.filename;
            document.getElementById('filePreview').style.display = 'flex';
            document.getElementById('fileName').textContent = file.name;
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        alert('Error uploading file');
    }
}

// Clear File
function clearFile() {
    uploadedFile = null;
    document.getElementById('filePreview').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

// Send Message
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    userInput.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                language: currentLanguage,
                file: uploadedFile
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (data.success) {
            addMessage(data.response, 'bot');
            
            // Text to speech
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(data.response);
                utterance.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
                speechSynthesis.speak(utterance);
            }
        } else {
            addMessage('Error: ' + data.message, 'bot');
        }
        
        clearFile();
    } catch (error) {
        removeTypingIndicator(typingId);
        console.error('Error:', error);
        addMessage('Sorry, something went wrong. Please try again.', 'bot');
    }
}

// Add Message to Chat
function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble ${sender}-message`;
    
    const textDiv = document.createElement('div');
    textDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    const now = new Date();
    timeDiv.textContent = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.appendChild(textDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    // Remove welcome message if exists
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add Typing Indicator
function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message-bubble bot-message';
    typingDiv.id = 'typing-' + Date.now();
    typingDiv.innerHTML = '<div>typing...</div>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingDiv.id;
}

// Remove Typing Indicator
function removeTypingIndicator(id) {
    const typing = document.getElementById(id);
    if (typing) {
        typing.remove();
    }
}

// Handle Enter Key
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Logout
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        console.error('Error logging out:', error);
    }
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('userInput');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Set initial language
    if (recognition) {
        recognition.lang = 'hi-IN';
    }
});