import { useState, useEffect, useRef } from 'react';
import Message from './Message';
import '../ChatPage.css';
import { API_BASE, ENDPOINTS } from '../apiConfig';

function ChatSearchString({ chatHash }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [searchString, setSearchString] = useState('');
  const [searchStringFormat, setSearchStringFormat] = useState('');
  const [availableFormats, setAvailableFormats] = useState([]);
  const [showFormatsDropdown, setShowFormatsDropdown] = useState(false);
  const [loadingConversion, setLoadingConversion] = useState(false);
  const [error, setError] = useState(null);

  const chatRef = useRef(null);

  useEffect(() => {
    const getChat = async () => {
      try {
        const response = await fetch(`${API_BASE}${ENDPOINTS.getChatHistory}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hash_plain_text: chatHash }),
        });

        return await response.json();
      } catch (err) {
        console.error('Error:', err);
        setError('An error occurred while getting chat.');
        return null;
      }
    };

    const populateChatHistory = async () => {
      const data = await getChat();
      const formattedMessages = [];

      if (data?.status && Array.isArray(data.chat_history)) {
        data.chat_history.forEach((entry) => {
          if (entry.user_message?.trim()) {
            formattedMessages.push({
              sender: 'user',
              title: 'You',
              message: entry.user_message,
            });
          }

          if (entry.llm_response?.trim()) {
            formattedMessages.push({
              sender: 'ai',
              title: 'SLRmentor',
              message: entry.llm_response,
              showSources: true,
            });
          }
        });

        const lastEntry = data.chat_history[data.chat_history.length - 1];

        if (lastEntry?.search_string) {
          setSearchString(lastEntry.search_string);
        }

        if (lastEntry?.search_string_format) {
          setSearchStringFormat(lastEntry.search_string_format);
        }
      }

      if (formattedMessages.length === 0) {
        formattedMessages.push({
          sender: 'ai',
          title: 'SLRmentor',
          message:
            'Hello👋 I am SLRmentor. Give me your study goal and I will help you create your search string!',
          showSources: true,
        });
      }

      setMessages(formattedMessages);
    };

    if (chatHash) {
      populateChatHistory();
    }
  }, [chatHash]);

  useEffect(() => {
    const fetchFormats = async () => {
      try {
        const response = await fetch(`${API_BASE}${ENDPOINTS.conversionFormats}`);
        const data = await response.json();

        if (Array.isArray(data.formats)) {
          setAvailableFormats(data.formats);
        }
      } catch (err) {
        console.error('Error fetching formats:', err);
      }
    };

    fetchFormats();
  }, []);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTo({
        top: chatRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        title: 'You',
        message: newMessage,
      },
    ]);

    try {
      const response = await fetch(`${API_BASE}${ENDPOINTS.prompt}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hash_plain_text: chatHash,
          user_message: newMessage,
        }),
      });

      const data = await response.json();

      if (data.status === true && data.llm_response?.trim()) {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'ai',
            title: 'SLRmentor',
            message: data.llm_response,
            showSources: true,
          },
        ]);

        setSearchString(data.updated_search_string || '');
        setSearchStringFormat(data.search_string_format || data.current_format || '');
      }
    } catch (err) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          title: 'SLRmentor',
          message: 'Error sending message.',
          showSources: true,
        },
      ]);
    }

    setNewMessage('');
  };

  const convertFormat = async (newFormat) => {
    if (!searchString) return;

    setLoadingConversion(true);
    setError(null);

    try {
      if (!ENDPOINTS.convertSearchString) {
        setError('Format conversion endpoint is not configured.');
        return;
      }

      const response = await fetch(`${API_BASE}${ENDPOINTS.convertSearchString}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hash_plain_text: chatHash,
          conversion_format: newFormat,
        }),
      });

      const data = await response.json();

      if (data?.status === true) {
        if (data.user_message?.trim()) {
          setMessages((prev) => [
            ...prev,
            {
              sender: 'user',
              title: 'You',
              message: data.user_message,
            },
          ]);
        }

        if (data.llm_response?.trim()) {
          setMessages((prev) => [
            ...prev,
            {
              sender: 'ai',
              title: 'SLRmentor',
              message: data.llm_response,
              showSources: true,
            },
          ]);
        }

        setSearchString(data.updated_search_string || searchString);
        setSearchStringFormat(data.current_format || newFormat);
        setShowFormatsDropdown(false);
      } else {
        setError('Format conversion was not successful.');
      }
    } catch (err) {
      console.error(err);
      setError('An error occurred while converting formats.');
    } finally {
      setLoadingConversion(false);
    }
  };

  return (
    <div className="chat-container">
      <h2 className="chat-header">Chat for Search String</h2>

      <div ref={chatRef} className="chat-history" id="search-chat-history">
        {messages.map((msg, i) => (
          <Message
            key={i}
            sender={msg.sender}
            title={msg.title}
            message={msg.message}
            showSources={msg.showSources || false}
          />
        ))}
      </div>

      {searchString && (
        <div className="search-string-div" id="search-string-panel">
          <pre className="search-string">{searchString}</pre>

          <div className="format-display-row">
            <span className="search-string-format" id="search-string-current-format">
              <strong>Current Format:</strong> {searchStringFormat || 'General'}
            </span>

            <button
              id="search-string-different-formats"
              className="formats-toggle-button"
              onClick={() => setShowFormatsDropdown((prev) => !prev)}
              disabled={loadingConversion}
              title={loadingConversion ? 'Processing...' : 'Select different format'}
            >
              Different Formats
            </button>
          </div>

          {showFormatsDropdown && (
            <ul className="formats-dropdown" id="search-string-formats-dropdown">
              {availableFormats
                .filter((format) => format !== searchStringFormat)
                .map((format, idx) => (
                  <li key={idx}>
                    <button
                      type="button"
                      className="formats-dropdown-item"
                      onClick={() => convertFormat(format)}
                      disabled={loadingConversion}
                    >
                      {format}
                    </button>
                  </li>
                ))}
            </ul>
          )}

          <button
            id="search-string-copy"
            className="copy-button"
            onClick={() => navigator.clipboard.writeText(searchString)}
          >
            Copy Search String
          </button>
        </div>
      )}

      <div className="chat-input-container">
        <input
          id="search-chat-input"
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Give me your study goal and I will help you create your search string!"
          className="chat-input"
          disabled={loadingConversion}
        />

        <button
          id="search-send-button"
          onClick={sendMessage}
          className="send-button"
          disabled={loadingConversion}
        >
          Send
        </button>
      </div>

      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}
    </div>
  );
}

export default ChatSearchString;