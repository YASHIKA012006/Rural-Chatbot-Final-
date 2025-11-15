from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database import init_db, add_user, get_user, add_message, get_user_messages, update_user_profile

app = Flask(__name__)
app.secret_key = '12345'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

init_db()

def get_ai_response(message, language='hi'):
    """Get AI response using Google Gemini API"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key='AIzaSyDNLvZjhcsEk4vnizwq0pgTt9yh_IKbId4') 
   
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        if language == 'hi':
            context = """आप एक सहायक AI चैटबॉट हैं जो ग्रामीण भारत के लोगों की मदद करते हैं।
सरल हिंदी में जवाब दें। किसानों, छात्रों और ग्रामीण लोगों की समस्याओं का समाधान दें।
कृषि, शिक्षा, स्वास्थ्य और सरकारी योजनाओं के बारे में जानकारी दें।

उपयोगकर्ता का सवाल: """
        else:
            context = """You are a helpful AI chatbot for rural India.
Answer in simple English. Help farmers, students and rural people.
Provide information about agriculture, education, health and government schemes.

User question: """
        
        response = model.generate_content(context + message)
        return response.text
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return get_fallback_response(message, language)

def get_fallback_response(message, language='hi'):
    """Fallback response when Gemini API fails"""
    message_lower = message.lower()
    
    if language == 'hi':
        responses = {
            'नमस्ते': 'नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ? 🙏',
            'हेलो': 'नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ? 🙏',
            'कैसे': 'मैं बहुत अच्छा हूँ, धन्यवाद! आप कैसे हैं?',
            'खेती': 'खेती के बारे में आपका क्या सवाल है? मैं फसल, सिंचाई, उर्वरक आदि के बारे में बता सकता हूँ। 🌾',
            'फसल': 'कौन सी फसल के बारे में जानना चाहते हैं? गेहूं, धान, मक्का, दाल या कोई और?',
            'मौसम': 'मौसम की जानकारी के लिए आप अपने क्षेत्र का नाम बताएं। ☀️',
            'सरकारी योजना': 'प्रधानमंत्री किसान सम्मान निधि, फसल बीमा योजना, मुद्रा लोन जैसी कई योजनाएं हैं। किस के बारे में जानना चाहते हैं?',
            'शिक्षा': 'शिक्षा से जुड़ी कोई भी जानकारी के लिए पूछें - छात्रवृत्ति, ऑनलाइन कोर्स, परीक्षा आदि। 📚',
            'स्वास्थ्य': 'स्वास्थ्य संबंधी सामान्य जानकारी दे सकता हूँ। गंभीर समस्या के लिए डॉक्टर से संपर्क करें। 🏥',
            'धन्यवाद': 'आपका स्वागत है! और कुछ मदद चाहिए? 😊',
            'default': 'मैं आपकी मदद करना चाहता हूँ। कृपया अपना सवाल विस्तार से पूछें। 🙏'
        }
    else:
        responses = {
            'hello': 'Hello! How can I help you? 🙏',
            'hi': 'Hi! How can I assist you today? 🙏',
            'how': 'I am doing great, thank you! How are you?',
            'farming': 'What would you like to know about farming? I can help with crops, irrigation, fertilizers, etc. 🌾',
            'crop': 'Which crop would you like to know about? Wheat, rice, corn, or others?',
            'weather': 'Please tell me your location for weather information. ☀️',
            'government scheme': 'There are many schemes like PM-KISAN, Crop Insurance, Mudra Loan. Which one would you like to know about?',
            'education': 'Ask me anything about education - scholarships, online courses, exams, etc. 📚',
            'health': 'I can provide general health information. For serious issues, please consult a doctor. 🏥',
            'thank': 'You are welcome! Need anything else? 😊',
            'default': 'I want to help you. Please ask your question in detail. 🙏'
        }
    
    for keyword, response in responses.items():
        if keyword in message_lower:
            return response
    
    return responses['default']

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'सभी फील्ड भरें / Fill all fields'})
    
    if get_user(email):
        return jsonify({'success': False, 'message': 'यह ईमेल पहले से मौजूद है / Email already exists'})
    
    hashed_password = generate_password_hash(password)
    user_id = add_user(name, email, hashed_password)
    
    return jsonify({'success': True, 'message': 'पंजीकरण सफल / Registration successful'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = get_user(email)
    
    if user and check_password_hash(user[3], password):
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['user_email'] = user[2]
        return jsonify({'success': True, 'message': 'लॉगिन सफल / Login successful'})
    
    return jsonify({'success': False, 'message': 'गलत ईमेल या पासवर्ड / Invalid credentials'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    user_message = data.get('message')
    language = data.get('language', 'hi')
    
    try:
        bot_response = get_ai_response(user_message, language)
        
        add_message(session['user_id'], user_message, bot_response)
        
        return jsonify({
            'success': True,
            'response': bot_response
        })
    
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath
        })
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    user = get_user(session['user_email'])
    return jsonify({
        'success': True,
        'profile': {
            'name': user[1],
            'email': user[2],
            'created_at': user[4]
        }
    })

@app.route('/api/profile', methods=['POST'])
def api_update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    name = data.get('name')
    
    if name:
        update_user_profile(session['user_id'], name)
        session['user_name'] = name
        return jsonify({'success': True, 'message': 'Profile updated'})
    
    return jsonify({'success': False, 'message': 'Invalid data'})

@app.route('/api/messages', methods=['GET'])
def api_get_messages():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    messages = get_user_messages(session['user_id'])
    return jsonify({
        'success': True,
        'messages': messages
    })

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)