# Telegram Bot Setup

Step-by-step guide to create and configure a Telegram bot for OpenCode Cloudify.

## Step 1: Create a Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts:
   - Enter a name for your bot (e.g., "My OpenCode Assistant")
   - Enter a username (must end in `bot`, e.g., `my_opencode_bot`)
4. Save the **API token** provided

## Step 2: Configure the Bot

Send these commands to BotFather:

```
/setdescription
```
Enter: "AI coding assistant powered by OpenCode"

```
/setabouttext
```
Enter: "Control your OpenCode instance from Telegram"

```
/setcommands
```
Enter:
```
start - Start using the bot
status - Current instance status
list - List all bound instances
switch - Switch active instance
web - Get Web Terminal link
cancel - Cancel current task
help - Show help message
```

## Step 3: Set Your Token

### Docker

```bash
docker run -d \
  -e TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz \
  ...
```

### Environment Variable

```bash
export TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Config File

```yaml
telegram:
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

## Step 4: Test the Bot

1. Start OpenCode Cloudify
2. Open your bot in Telegram
3. Send `/start`
4. You should receive a welcome message

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize and show welcome message |
| `/status` | Show current instance status |
| `/list` | List all bound OpenCode instances |
| `/switch <name>` | Switch to a different instance |
| `/web` | Get link to web terminal |
| `/cancel` | Cancel the current running task |
| `/help` | Show help message |

## Binding an Instance

1. Send `/start` to the bot
2. The bot will generate a QR code
3. Scan the QR code with the OpenCode CLI or web interface
4. Once bound, you can send messages directly to the AI

## Message Format

- **Text messages**: Sent directly to OpenCode
- **Images**: Attached to your message (for context)
- **Files**: Uploaded and available to OpenCode

## Tips

- Use `/cancel` if the AI is taking too long
- Long code responses are rendered as images for mobile viewing
- Use `/web` to access the full terminal when needed
