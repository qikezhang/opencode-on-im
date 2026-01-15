# DingTalk Bot Setup

Guide to create and configure a DingTalk bot for OpenCode Cloudify.

## Prerequisites

- DingTalk Enterprise account (or DingTalk Open Platform developer account)
- Admin access to create applications

## Step 1: Create an Application

1. Go to [DingTalk Open Platform](https://open.dingtalk.com/)
2. Log in with your account
3. Navigate to **Application Development** > **Enterprise Internal Applications**
4. Click **Create Application**
5. Fill in the application details:
   - Name: "OpenCode Assistant"
   - Description: "AI coding assistant"
   - Icon: Upload an icon

## Step 2: Enable Robot Capability

1. In your application settings, go to **Add Capability**
2. Select **Robot**
3. Configure the robot:
   - Message receiving mode: **Stream Mode** (recommended)
   - Robot name: "OpenCode"

## Step 3: Get Credentials

In your application's **Credentials and Basic Information**:

1. Copy the **AppKey**
2. Copy the **AppSecret**
3. Note the **AgentId** (optional, for some features)

## Step 4: Configure OpenCode Cloudify

### Docker

```bash
docker run -d \
  -e DINGTALK_APP_KEY=your_app_key \
  -e DINGTALK_APP_SECRET=your_app_secret \
  ...
```

### Config File

```yaml
dingtalk:
  app_key: "your_app_key"
  app_secret: "your_app_secret"
  agent_id: "your_agent_id"  # Optional
```

## Step 5: Deploy and Test

1. Start OpenCode Cloudify
2. In DingTalk, search for your bot
3. Send a message to test

## Message Cards

DingTalk supports rich message cards. OpenCode Cloudify uses:

- **Status Cards**: Show instance status with action buttons
- **Code Output Cards**: Display code with syntax highlighting info
- **Error Cards**: Show errors with troubleshooting tips

## Stream Mode vs Webhook

OpenCode Cloudify uses **Stream Mode** which:

- Does not require a public IP
- Works behind firewalls
- Maintains a persistent connection
- Lower latency than webhooks

## Troubleshooting

### Bot not responding

1. Verify AppKey and AppSecret are correct
2. Check that Stream Mode is enabled
3. View logs: `docker logs opencode-cloudify`

### Permission errors

Ensure your application has the required permissions:
- Robot message sending
- Group chat access (if using in groups)

## Group Chat Usage

To use in group chats:

1. Enable group chat in robot settings
2. Add the bot to your group
3. @mention the bot to interact

## Security Notes

- Keep your AppSecret secure
- Use environment variables, not hardcoded values
- Rotate credentials if compromised
