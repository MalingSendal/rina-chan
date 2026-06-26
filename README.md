# Rina-chan AI Companion

A web-based AI companion featuring Live2D animation and personality-driven chat powered by Ollama.

## Features

- ✨ **Live2D Animation** - Beautiful animated character model
- 💬 **Personality Chat** - Innocent, bratty, and engaging personality
- 🔒 **NSFW Toggle** - Switch between normal and flirty modes with a slider
- 🎨 **Simplistic UI** - Modern chat interface with smooth animations
- ⚙️ **Easy Configuration** - IP and model settings in `.env` file
- 🚀 **Ollama Integration** - Uses local Ollama LLM for localized, and private responses

## Prerequisites

- **Ollama** installed and running (download from [ollama.ai](https://ollama.ai))
- **Python 3.8+** installed
- **A Llama model** pulled in Ollama (e.g., `ollama pull llama3.2:3b`)
- In Ollama make sure to turn on its "Expose Ollama to the network" settings

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Ollama Connection

Edit `.env` file with your Ollama settings:

```env
OLLAMA_IP=192.168.100.XX       # Your Ollama server IP
OLLAMA_PORT=11434              # Ollama API port (default 11434)
OLLAMA_MODEL=llama3.2:3b       # Model name to use
CHARACTER_NAME=Rina-chan       # Default Character name (no need to change this)
USER=Ren                       # Change this if you want her to refer to your name
APP_IP=192.168.XXX.XX          # Your Local IP Address
```

### 3. Start Ollama

Make sure Ollama is running on the configured IP:port. If running locally:

```bash
ollama serve
```

If using a remote Ollama server, ensure it's accessible and the firewall allows connections.

### 4. Start the Backend Server

```bash
python app.py
```

You should see:
```
╔══════════════════════════════════════╗
║   Rina-chan AI Companion Backend     ║
╚══════════════════════════════════════╝

Configuration:
- Ollama IP: 192.168.XXX.XX
- Ollama Port: 11434
- Model: mistral
- Character: Rina-chan
- User Name : Ren

Starting server on http://APP_IP:5000
✓ Ollama is reachable! Available models:
  - mistral
  - neural-chat
  - llama3.2:3b
  ...
```

### 5. Open the Web Interface

Open `index.html` in a web browser (or serve it with a local HTTP server):

```bash
# Option 1: Simple Python HTTP server
python -m http.server 8000

# Option 2: Using Live Server extension in VS Code
# Click "Go Live" in the status bar
```

Then navigate to `http://localhost:8000` (or your server URL)

## How to Use

1. **Type your message** in the chat input at the bottom
2. **Press Enter or click Send** to send your message
3. **Toggle NSFW** with the slider in the chat header for flirty / cruel mode
4. **The model will respond** with Rina-chan's personality

## Configuration

### Change the Ollama Model

Edit `.env`:
```env
OLLAMA_MODEL=neural-chat  # or any other pulled model
```

### Change Ollama Server IP

If using a remote Ollama server:
```env
OLLAMA_IP=192.168.XXX.XX  # Your remote IP
```

### Customize Personality

Edit the `SYSTEM_PROMPT` and `SYSTEM_PROMPT_NSFW` in `app.py` to modify her personality.

## Troubleshooting

### "Cannot reach Ollama"
- Check that Ollama is running
- Verify the IP and port are correct
- Test with: `curl http://192.168.XXX.XX:11434/api/tags`

### Chat not responding
- Check the browser console (F12) for errors
- Check the Python terminal for server logs
- Make sure the model is actually pulled: `ollama list`

### Model not found
- Pull the model first: `ollama pull mistral`
- Or pull another model: `ollama pull neural-chat`

## File Structure

```
rina-chan/
├── index.html           # Web interface with Live2D and chat
├── app.py              # Flask backend server
├── requirements.txt    # Python dependencies
├── .env                # Configuration (IP, model, etc.)
├── .env.example        # Example configuration
├── js/                 # JavaScript libraries (PixiJS, Live2D)
├── KITU_RE23/          # Live2D model files
└── README.md           # This file
```

## Available Endpoints

- `POST /chat` - Send a chat message
  - Body: `{"message": "...", "nsfw_mode": false}`
  - Response: `{"response": "..."}`

- `GET /config` - Get current configuration
  - Response: `{"ollama_ip": "...", "ollama_model": "...", ...}`

- `GET /health` - Check Ollama connection
  - Response: `{"status": "ok", "available_models": [...]}`

## Personality Details

### Normal Mode
- Sweet and innocent
- Playful and teasing
- Uses cute expressions
- Kind and friendly

### NSFW Mode
- More flirty and forward
- Confident and charming
- Still respectful and classy
- Teases more boldly

## Tips

- Use shorter models like `llama3.2:3b` or `mistral` for faster responses
- Adjust temperature in `app.py` for more/less random responses
- Keep chat history for better context (up to 50 messages stored)

## Support

If you encounter issues:
1. Check the console output (browser F12 and Python terminal)
2. Verify Ollama is running and accessible
3. Make sure the model is pulled in Ollama
4. Check your `.env` configuration
