#!/bin/bash
set -e

REPO="qikezhang/opencode-on-im"

echo "Creating labels..."
gh label create "week-1" --color "0E8A16" --repo $REPO 2>/dev/null || true
gh label create "week-2" --color "1D76DB" --repo $REPO 2>/dev/null || true
gh label create "week-3" --color "5319E7" --repo $REPO 2>/dev/null || true
gh label create "week-4" --color "FBCA04" --repo $REPO 2>/dev/null || true
gh label create "week-5" --color "D93F0B" --repo $REPO 2>/dev/null || true
gh label create "week-6" --color "B60205" --repo $REPO 2>/dev/null || true
gh label create "infrastructure" --color "C5DEF5" --repo $REPO 2>/dev/null || true
gh label create "core" --color "BFD4F2" --repo $REPO 2>/dev/null || true
gh label create "adapter" --color "D4C5F9" --repo $REPO 2>/dev/null || true
gh label create "render" --color "FEF2C0" --repo $REPO 2>/dev/null || true
gh label create "docker" --color "F9D0C4" --repo $REPO 2>/dev/null || true
gh label create "docs" --color "0075CA" --repo $REPO 2>/dev/null || true
gh label create "test" --color "E99695" --repo $REPO 2>/dev/null || true
gh label create "release" --color "006B75" --repo $REPO 2>/dev/null || true
gh label create "telegram" --color "0088CC" --repo $REPO 2>/dev/null || true
gh label create "dingtalk" --color "007AFF" --repo $REPO 2>/dev/null || true
gh label create "opencode" --color "6E5494" --repo $REPO 2>/dev/null || true
gh label create "ux" --color "FFC0CB" --repo $REPO 2>/dev/null || true

echo "Creating Week 1 issues..."
gh issue create --repo $REPO --title "[INFRA] Project structure initialization + Poetry config" --label "infrastructure,week-1" --body "Initialize the project with proper Python packaging structure.

**Tasks:**
- [x] Create directory structure per SPECIFICATION.md
- [x] Configure pyproject.toml with all dependencies
- [x] Add .gitignore, LICENSE, README.md
- [x] Set up Poetry for dependency management

**Acceptance Criteria:**
- \`poetry install\` succeeds
- Project structure matches specification"

gh issue create --repo $REPO --title "[INFRA] GitHub Actions CI/CD configuration" --label "infrastructure,week-1" --body "Set up continuous integration and deployment pipelines.

**Tasks:**
- [x] Create ci.yml for testing and linting
- [x] Create release.yml for PyPI and Docker Hub publishing
- [ ] Configure GitHub secrets documentation

**Acceptance Criteria:**
- CI runs on every PR
- Release workflow triggers on version tags"

gh issue create --repo $REPO --title "[CORE] Configuration management module (pydantic-settings)" --label "core,week-1" --body "Implement type-safe configuration management.

**Tasks:**
- [x] Create Settings class with pydantic-settings
- [x] Support environment variables
- [x] Support YAML config files
- [x] Add validation for required fields

**Acceptance Criteria:**
- Settings load from env vars and config file
- Type errors caught at startup"

gh issue create --repo $REPO --title "[CORE] Persistence layer implementation (storage.py)" --label "core,week-1" --body "Implement data persistence for bindings and messages.

**Tasks:**
- [x] Create SQLite database schema
- [x] Implement bindings CRUD operations
- [x] Implement offline message queue
- [ ] Add database migrations support

**Acceptance Criteria:**
- Data persists across restarts
- Concurrent access handled safely"

gh issue create --repo $REPO --title "[CORE] Adapter abstract interface definition" --label "core,week-1" --body "Define the base interface for IM platform adapters.

**Tasks:**
- [x] Create BaseAdapter ABC
- [x] Define message sending methods
- [x] Define event receiving interface
- [x] Create IncomingMessage dataclass

**Acceptance Criteria:**
- Interface is complete and documented
- Type hints are correct"

echo "Creating Week 2 issues..."
gh issue create --repo $REPO --title "[ADAPTER] aiogram Bot basic framework" --label "adapter,telegram,week-2" --body "Set up the Telegram bot using aiogram 3.x.

**Tasks:**
- [x] Initialize Bot and Dispatcher
- [x] Configure polling mode
- [x] Implement start/stop lifecycle
- [x] Add structured logging

**Acceptance Criteria:**
- Bot connects to Telegram API
- Graceful shutdown works"

gh issue create --repo $REPO --title "[ADAPTER] Telegram message handler" --label "adapter,telegram,week-2" --body "Handle incoming messages from Telegram users.

**Tasks:**
- [x] Text message handler
- [x] Voice message handler (pass-through)
- [x] QR code binding handler
- [ ] Error handling and user feedback

**Acceptance Criteria:**
- Messages are received and logged
- Errors don't crash the bot"

gh issue create --repo $REPO --title "[ADAPTER] Telegram command router" --label "adapter,telegram,week-2" --body "Implement all bot commands.

**Tasks:**
- [x] /start, /help commands
- [x] /status, /list commands
- [x] /switch, /rename commands
- [x] /web, /cancel commands

**Acceptance Criteria:**
- All commands respond correctly
- Help text is accurate"

gh issue create --repo $REPO --title "[ADAPTER] Markdown formatter for Telegram" --label "adapter,telegram,week-2" --body "Format OpenCode output for Telegram MarkdownV2.

**Tasks:**
- [x] Escape special characters
- [ ] Format code blocks
- [ ] Format inline code
- [ ] Handle long messages (split)

**Acceptance Criteria:**
- Messages render correctly in Telegram
- No markdown parsing errors"

gh issue create --repo $REPO --title "[ADAPTER] Image sending support for Telegram" --label "adapter,telegram,week-2" --body "Send images (code screenshots) via Telegram.

**Tasks:**
- [x] Implement send_image method
- [ ] Add caption support
- [ ] Handle image size limits
- [ ] Compress if needed

**Acceptance Criteria:**
- Images display correctly
- Large images are handled"

echo "Creating Week 3 issues..."
gh issue create --repo $REPO --title "[CORE] OpenCode SDK client wrapper" --label "core,opencode,week-3" --body "Wrap OpenCode SDK for internal use.

**Tasks:**
- [x] HTTP client setup with httpx
- [x] Session CRUD methods
- [x] Message sending
- [ ] Error handling and retries

**Acceptance Criteria:**
- Can create sessions
- Can send messages
- Errors are handled gracefully"

gh issue create --repo $REPO --title "[CORE] Event subscription + output forwarding" --label "core,opencode,week-3" --body "Subscribe to OpenCode events and forward to IM.

**Tasks:**
- [x] SSE event subscription
- [x] Event parsing
- [x] Callback mechanism
- [ ] Reconnection logic

**Acceptance Criteria:**
- Events are received in real-time
- Reconnects on disconnect"

gh issue create --repo $REPO --title "[CORE] QR code generation + signing" --label "core,week-3" --body "Generate secure QR codes for instance binding.

**Tasks:**
- [x] QR data structure design
- [x] HMAC signing
- [x] QR image generation
- [x] Terminal ASCII QR display

**Acceptance Criteria:**
- QR codes are scannable
- Signatures are verified correctly"

gh issue create --repo $REPO --title "[CORE] Binding verification + user management" --label "core,week-3" --body "Verify QR codes and manage user bindings.

**Tasks:**
- [x] Secret verification
- [x] Bind/unbind operations
- [x] Multi-user per instance
- [ ] Binding expiration check

**Acceptance Criteria:**
- Valid QR codes bind successfully
- Invalid codes are rejected"

gh issue create --repo $REPO --title "[CORE] Multi-instance session management" --label "core,week-3" --body "Manage multiple OpenCode instances per user.

**Tasks:**
- [x] Instance registry
- [x] Active instance tracking
- [x] Instance naming
- [x] Instance switching

**Acceptance Criteria:**
- Users can bind multiple instances
- Switching works correctly"

echo "Creating Week 4 issues..."
gh issue create --repo $REPO --title "[ADAPTER] DingTalk SDK integration" --label "adapter,dingtalk,week-4" --body "Integrate DingTalk enterprise bot SDK.

**Tasks:**
- [x] SDK initialization
- [ ] Message receiving
- [ ] Long-polling setup
- [ ] Error handling

**Acceptance Criteria:**
- Bot connects to DingTalk
- Messages are received"

gh issue create --repo $REPO --title "[ADAPTER] DingTalk message card format" --label "adapter,dingtalk,week-4" --body "Format messages as DingTalk cards.

**Tasks:**
- [ ] Card template design
- [ ] Action button support
- [ ] Link embedding
- [ ] Markdown conversion

**Acceptance Criteria:**
- Cards display correctly
- Buttons work"

gh issue create --repo $REPO --title "[RENDER] Code highlighting renderer (Pygments)" --label "render,week-4" --body "Render code with syntax highlighting.

**Tasks:**
- [x] Lexer selection
- [x] Style configuration
- [x] Line number support
- [ ] Theme options

**Acceptance Criteria:**
- Code is highlighted correctly
- Multiple languages supported"

gh issue create --repo $REPO --title "[RENDER] Code to image converter (Pillow)" --label "render,week-4" --body "Convert code blocks to PNG images.

**Tasks:**
- [x] Image generation
- [x] Font configuration
- [ ] Size optimization
- [ ] Mobile-friendly dimensions

**Acceptance Criteria:**
- Images are readable on mobile
- File size is reasonable"

gh issue create --repo $REPO --title "[CORE] Auto-convert long content to image" --label "core,week-4" --body "Automatically convert long outputs to images.

**Tasks:**
- [x] Line count threshold check
- [x] Trigger image rendering
- [ ] Caption generation
- [ ] Fallback handling

**Acceptance Criteria:**
- Long messages become images
- Threshold is configurable"

echo "Creating Week 5 issues..."
gh issue create --repo $REPO --title "[DOCKER] Dockerfile creation" --label "docker,week-5" --body "Create production Docker image.

**Tasks:**
- [x] Multi-stage build
- [x] Dependency installation
- [x] Font installation for rendering
- [ ] Size optimization

**Acceptance Criteria:**
- Image builds successfully
- Size < 500MB (slim)"

gh issue create --repo $REPO --title "[DOCKER] s6-overlay process management" --label "docker,week-5" --body "Configure s6-overlay for multiple processes.

**Tasks:**
- [ ] s6-overlay installation
- [ ] Service definitions
- [ ] Health checks
- [ ] Graceful shutdown

**Acceptance Criteria:**
- All services start correctly
- Restart on failure works"

gh issue create --repo $REPO --title "[DOCKER] ttyd integration + switching support" --label "docker,week-5" --body "Integrate web terminal for browser access.

**Tasks:**
- [ ] ttyd installation
- [ ] Port configuration
- [ ] Authentication (optional)
- [ ] code-server switch support

**Acceptance Criteria:**
- Web terminal accessible
- Terminal is functional"

gh issue create --repo $REPO --title "[CORE] Proxy configuration module" --label "core,week-5" --body "Support residential proxy configuration.

**Tasks:**
- [x] Environment variable support
- [x] Config file support
- [ ] Runtime configuration via bot
- [ ] Proxy status check

**Acceptance Criteria:**
- Proxy can be configured
- Traffic routes through proxy"

gh issue create --repo $REPO --title "[UX] First-run setup wizard" --label "ux,week-5" --body "Interactive setup for first-time users.

**Tasks:**
- [x] Token input prompts
- [x] Proxy configuration
- [x] Config file generation
- [ ] Validation feedback

**Acceptance Criteria:**
- Setup completes successfully
- Config is valid"

echo "Creating Week 6 issues..."
gh issue create --repo $REPO --title "[DOCS] README + installation guide" --label "docs,week-6" --body "Write comprehensive documentation.

**Tasks:**
- [x] README with quick start
- [ ] Detailed installation guide
- [ ] Troubleshooting section
- [ ] FAQ

**Acceptance Criteria:**
- New users can get started
- Common issues are addressed"

gh issue create --repo $REPO --title "[DOCS] Proxy best practices (with affiliate links)" --label "docs,week-6" --body "Guide for using residential proxies.

**Tasks:**
- [ ] Why proxies are needed
- [ ] Provider recommendations
- [ ] Configuration steps
- [ ] Troubleshooting

**Acceptance Criteria:**
- Users understand when to use proxy
- Links are properly embedded"

gh issue create --repo $REPO --title "[DOCS] DigitalOcean deployment guide" --label "docs,week-6" --body "Step-by-step DO deployment tutorial.

**Tasks:**
- [ ] One-click deploy setup
- [ ] Manual deployment steps
- [ ] Environment configuration
- [ ] Domain/SSL setup

**Acceptance Criteria:**
- Users can deploy to DO
- Affiliate link works"

gh issue create --repo $REPO --title "[TEST] Unit tests + integration tests" --label "test,week-6" --body "Comprehensive test coverage.

**Tasks:**
- [x] Test configuration
- [ ] Core module tests
- [ ] Adapter tests (mocked)
- [ ] Integration tests

**Acceptance Criteria:**
- Coverage > 70%
- All tests pass"

gh issue create --repo $REPO --title "[RELEASE] PyPI + Docker Hub publishing" --label "release,week-6" --body "Publish packages to registries.

**Tasks:**
- [ ] PyPI account setup
- [ ] Docker Hub account setup
- [ ] Version tagging
- [ ] Release notes

**Acceptance Criteria:**
- Package installable via pip
- Image pullable from Docker Hub"

echo ""
echo "✅ All 30 issues created successfully!"
echo ""
echo "View issues: https://github.com/qikezhang/opencode-on-im/issues"
