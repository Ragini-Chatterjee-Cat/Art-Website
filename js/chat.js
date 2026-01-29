/**
 * Inside the Paintbox - AI Chat Widget
 * Connects to RAG backend to answer questions about artworks
 */

// ============================================
// CONFIGURATION - UPDATE THIS AFTER DEPLOYMENT
// ============================================
// For local development: 'http://localhost:8000'

const API_URL = 'https://art-website-production.up.railway.app';


// ============================================
// CHAT FUNCTIONALITY
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatBox = document.getElementById('chatBox');
    const chatClose = document.getElementById('chatClose');
    const chatBody = document.querySelector('.chat-body');
    const chatForm = document.querySelector('.chat-form');

    // Store conversation history for context
    let conversationHistory = [];

    // Replace the contact form with chat interface
    chatForm.innerHTML = `
        <div class="chat-input-container">
            <input
                type="text"
                id="userMessage"
                class="chat-input"
                placeholder="Ask for any queries..."
                autocomplete="on"
            >
            <button type="button" id="sendBtn" class="chat-send-btn">
                <i class="fa fa-paper-plane"></i>
            </button>
        </div>
    `;

    // Add custom styles for the new chat interface
    addChatStyles();

    // Open chat
    chatButton.addEventListener('click', function() {
        chatBox.classList.add('active');
        chatButton.style.display = 'none';
        document.getElementById('userMessage').focus();
    });

    // Close chat
    chatClose.addEventListener('click', function() {
        chatBox.classList.remove('active');
        chatButton.style.display = 'flex';
    });

    // Send message on button click
    document.getElementById('sendBtn').addEventListener('click', sendMessage);

    // Send message on Enter key
    document.getElementById('userMessage').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    /**
     * Send message to the RAG backend
     */
    async function sendMessage() {
        const input = document.getElementById('userMessage');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        input.value = '';
        input.disabled = true;

        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        try {
            // Call the RAG API with conversation history
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory
                })
            });

            if (!response.ok) {
                throw new Error('API request failed');
            }

            const data = await response.json();

            // Remove typing indicator and show response
            typingIndicator.remove();
            addMessage(data.response, 'bot');

            // Update conversation history
            conversationHistory.push({ role: 'user', content: message });
            conversationHistory.push({ role: 'assistant', content: data.response });

            // Keep only last 12 messages (6 exchanges) to avoid token limits
            if (conversationHistory.length > 12) {
                conversationHistory = conversationHistory.slice(-12);
            }

        } catch (error) {
            console.error('Chat error:', error);
            typingIndicator.remove();
            addMessage(
                "I'm sorry, can't connect to the server right now. Please try again later.",
                'bot'
            );
        }

        input.disabled = false;
        input.focus();
    }

    /**
     * Add a message to the chat
     */
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;
        messageDiv.textContent = text;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
        return messageDiv;
    }

    /**
     * Add typing indicator
     */
    function addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot typing';
        typingDiv.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
        chatBody.appendChild(typingDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
        return typingDiv;
    }

    /**
     * Add additional styles for the chat interface
     */
    function addChatStyles() {
        const styles = document.createElement('style');
        styles.textContent = `
            /* User messages */
            .chat-message.user {
                background: rgba(92, 64, 51, 0.15);
                color: #5c4033;
                align-self: flex-end;
                border-bottom-right-radius: 5px;
            }

            /* Chat input container */
            .chat-input-container {
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .chat-input-container .chat-input {
                flex: 1;
                margin-bottom: 0;
            }

            /* Send button */
            .chat-send-btn {
                width: 45px;
                height: 45px;
                border-radius: 50%;
                background: transparent;
                border: 2px solid #5c4033;
                color: #5c4033;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                flex-shrink: 0;
            }

            .chat-send-btn:hover {
                background: rgba(92, 64, 51, 0.15);
                color: #5c4033;
            }

            /* Typing indicator */
            .chat-message.typing {
                display: flex;
                gap: 4px;
                padding: 15px 20px;
            }

            .typing-dot {
                width: 8px;
                height: 8px;
                background: #5c4033;
                border-radius: 50%;
                animation: typingBounce 1.4s infinite ease-in-out both;
            }

            .typing-dot:nth-child(1) { animation-delay: -0.32s; }
            .typing-dot:nth-child(2) { animation-delay: -0.16s; }
            .typing-dot:nth-child(3) { animation-delay: 0s; }

            @keyframes typingBounce {
                0%, 80%, 100% {
                    transform: scale(0.6);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(styles);
    }
});
