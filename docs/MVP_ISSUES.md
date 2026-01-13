# MVP Development Issues (6 Weeks)

This document contains all 30 GitHub Issues for the MVP development phase.
Copy each issue to GitHub or use `gh issue create` to batch create them.

---

## Week 1: Project Infrastructure (5 Issues)

### Issue #1: [INFRA] Project structure initialization + Poetry config
**Labels:** `infrastructure`, `week-1`
**Priority:** P0

**Description:**
Initialize the project with proper Python packaging structure.

**Tasks:**
- [x] Create directory structure per SPECIFICATION.md
- [x] Configure pyproject.toml with all dependencies
- [x] Add .gitignore, LICENSE, README.md
- [x] Set up Poetry for dependency management

**Acceptance Criteria:**
- `poetry install` succeeds
- Project structure matches specification

---

### Issue #2: [INFRA] GitHub Actions CI/CD configuration
**Labels:** `infrastructure`, `week-1`
**Priority:** P0

**Description:**
Set up continuous integration and deployment pipelines.

**Tasks:**
- [x] Create ci.yml for testing and linting
- [x] Create release.yml for PyPI and Docker Hub publishing
- [ ] Configure GitHub secrets documentation

**Acceptance Criteria:**
- CI runs on every PR
- Release workflow triggers on version tags

---

### Issue #3: [CORE] Configuration management module (pydantic-settings)
**Labels:** `core`, `week-1`
**Priority:** P0

**Description:**
Implement type-safe configuration management.

**Tasks:**
- [x] Create Settings class with pydantic-settings
- [x] Support environment variables
- [x] Support YAML config files
- [x] Add validation for required fields

**Acceptance Criteria:**
- Settings load from env vars and config file
- Type errors caught at startup

---

### Issue #4: [CORE] Persistence layer implementation (storage.py)
**Labels:** `core`, `week-1`
**Priority:** P0

**Description:**
Implement data persistence for bindings and messages.

**Tasks:**
- [x] Create SQLite database schema
- [x] Implement bindings CRUD operations
- [x] Implement offline message queue
- [x] Add database migrations support

**Acceptance Criteria:**
- Data persists across restarts
- Concurrent access handled safely

---

### Issue #5: [CORE] Adapter abstract interface definition
**Labels:** `core`, `week-1`
**Priority:** P0

**Description:**
Define the base interface for IM platform adapters.

**Tasks:**
- [x] Create BaseAdapter ABC
- [x] Define message sending methods
- [x] Define event receiving interface
- [x] Create IncomingMessage dataclass

**Acceptance Criteria:**
- Interface is complete and documented
- Type hints are correct

---

## Week 2: Telegram Adapter (5 Issues)

### Issue #6: [ADAPTER] aiogram Bot basic framework
**Labels:** `adapter`, `telegram`, `week-2`
**Priority:** P0

**Description:**
Set up the Telegram bot using aiogram 3.x.

**Tasks:**
- [x] Initialize Bot and Dispatcher
- [x] Configure polling mode
- [x] Implement start/stop lifecycle
- [x] Add structured logging

**Acceptance Criteria:**
- Bot connects to Telegram API
- Graceful shutdown works

---

### Issue #7: [ADAPTER] Telegram message handler
**Labels:** `adapter`, `telegram`, `week-2`
**Priority:** P0

**Description:**
Handle incoming messages from Telegram users.

**Tasks:**
- [x] Text message handler
- [x] Voice message handler (pass-through)
- [x] QR code binding handler
- [ ] Error handling and user feedback

**Acceptance Criteria:**
- Messages are received and logged
- Errors don't crash the bot

---

### Issue #8: [ADAPTER] Telegram command router
**Labels:** `adapter`, `telegram`, `week-2`
**Priority:** P0

**Description:**
Implement all bot commands.

**Tasks:**
- [x] /start, /help commands
- [x] /status, /list commands
- [x] /switch, /rename commands
- [x] /web, /cancel commands

**Acceptance Criteria:**
- All commands respond correctly
- Help text is accurate

---

### Issue #9: [ADAPTER] Markdown formatter for Telegram
**Labels:** `adapter`, `telegram`, `week-2`
**Priority:** P1

**Description:**
Format OpenCode output for Telegram MarkdownV2.

**Tasks:**
- [x] Escape special characters
- [ ] Format code blocks
- [ ] Format inline code
- [ ] Handle long messages (split)

**Acceptance Criteria:**
- Messages render correctly in Telegram
- No markdown parsing errors

---

### Issue #10: [ADAPTER] Image sending support for Telegram
**Labels:** `adapter`, `telegram`, `week-2`
**Priority:** P1

**Description:**
Send images (code screenshots) via Telegram.

**Tasks:**
- [x] Implement send_image method
- [ ] Add caption support
- [ ] Handle image size limits
- [ ] Compress if needed

**Acceptance Criteria:**
- Images display correctly
- Large images are handled

---

## Week 3: OpenCode Integration (5 Issues)

### Issue #11: [CORE] OpenCode SDK client wrapper
**Labels:** `core`, `opencode`, `week-3`
**Priority:** P0

**Description:**
Wrap OpenCode SDK for internal use.

**Tasks:**
- [x] HTTP client setup with httpx
- [x] Session CRUD methods
- [x] Message sending
- [ ] Error handling and retries

**Acceptance Criteria:**
- Can create sessions
- Can send messages
- Errors are handled gracefully

---

### Issue #12: [CORE] Event subscription + output forwarding
**Labels:** `core`, `opencode`, `week-3`
**Priority:** P0

**Description:**
Subscribe to OpenCode events and forward to IM.

**Tasks:**
- [x] SSE event subscription
- [x] Event parsing
- [x] Callback mechanism
- [ ] Reconnection logic

**Acceptance Criteria:**
- Events are received in real-time
- Reconnects on disconnect

---

### Issue #13: [CORE] QR code generation + signing
**Labels:** `core`, `week-3`
**Priority:** P0

**Description:**
Generate secure QR codes for instance binding.

**Tasks:**
- [x] QR data structure design
- [x] HMAC signing
- [x] QR image generation
- [x] Terminal ASCII QR display

**Acceptance Criteria:**
- QR codes are scannable
- Signatures are verified correctly

---

### Issue #14: [CORE] Binding verification + user management
**Labels:** `core`, `week-3`
**Priority:** P0

**Description:**
Verify QR codes and manage user bindings.

**Tasks:**
- [x] Secret verification
- [x] Bind/unbind operations
- [x] Multi-user per instance
- [ ] Binding expiration check

**Acceptance Criteria:**
- Valid QR codes bind successfully
- Invalid codes are rejected

---

### Issue #15: [CORE] Multi-instance session management
**Labels:** `core`, `week-3`
**Priority:** P0

**Description:**
Manage multiple OpenCode instances per user.

**Tasks:**
- [x] Instance registry
- [x] Active instance tracking
- [x] Instance naming
- [x] Instance switching

**Acceptance Criteria:**
- Users can bind multiple instances
- Switching works correctly

---

## Week 4: DingTalk + Rendering (5 Issues)

### Issue #16: [ADAPTER] DingTalk SDK integration
**Labels:** `adapter`, `dingtalk`, `week-4`
**Priority:** P0

**Description:**
Integrate DingTalk enterprise bot SDK.

**Tasks:**
- [x] SDK initialization
- [ ] Message receiving
- [ ] Long-polling setup
- [ ] Error handling

**Acceptance Criteria:**
- Bot connects to DingTalk
- Messages are received

---

### Issue #17: [ADAPTER] DingTalk message card format
**Labels:** `adapter`, `dingtalk`, `week-4`
**Priority:** P1

**Description:**
Format messages as DingTalk cards.

**Tasks:**
- [ ] Card template design
- [ ] Action button support
- [ ] Link embedding
- [ ] Markdown conversion

**Acceptance Criteria:**
- Cards display correctly
- Buttons work

---

### Issue #18: [RENDER] Code highlighting renderer (Pygments)
**Labels:** `render`, `week-4`
**Priority:** P1

**Description:**
Render code with syntax highlighting.

**Tasks:**
- [x] Lexer selection
- [x] Style configuration
- [x] Line number support
- [ ] Theme options

**Acceptance Criteria:**
- Code is highlighted correctly
- Multiple languages supported

---

### Issue #19: [RENDER] Code to image converter (Pillow)
**Labels:** `render`, `week-4`
**Priority:** P0

**Description:**
Convert code blocks to PNG images.

**Tasks:**
- [x] Image generation
- [x] Font configuration
- [ ] Size optimization
- [ ] Mobile-friendly dimensions

**Acceptance Criteria:**
- Images are readable on mobile
- File size is reasonable

---

### Issue #20: [CORE] Auto-convert long content to image
**Labels:** `core`, `week-4`
**Priority:** P0

**Description:**
Automatically convert long outputs to images.

**Tasks:**
- [x] Line count threshold check
- [x] Trigger image rendering
- [ ] Caption generation
- [ ] Fallback handling

**Acceptance Criteria:**
- Long messages become images
- Threshold is configurable

---

## Week 5: Docker + Web (5 Issues)

### Issue #21: [DOCKER] Dockerfile creation
**Labels:** `docker`, `week-5`
**Priority:** P0

**Description:**
Create production Docker image.

**Tasks:**
- [x] Multi-stage build
- [x] Dependency installation
- [x] Font installation for rendering
- [ ] Size optimization

**Acceptance Criteria:**
- Image builds successfully
- Size < 500MB (slim)

---

### Issue #22: [DOCKER] s6-overlay process management
**Labels:** `docker`, `week-5`
**Priority:** P1

**Description:**
Configure s6-overlay for multiple processes.

**Tasks:**
- [ ] s6-overlay installation
- [ ] Service definitions
- [ ] Health checks
- [ ] Graceful shutdown

**Acceptance Criteria:**
- All services start correctly
- Restart on failure works

---

### Issue #23: [DOCKER] ttyd integration + switching support
**Labels:** `docker`, `web`, `week-5`
**Priority:** P0

**Description:**
Integrate web terminal for browser access.

**Tasks:**
- [ ] ttyd installation
- [ ] Port configuration
- [ ] Authentication (optional)
- [ ] code-server switch support

**Acceptance Criteria:**
- Web terminal accessible
- Terminal is functional

---

### Issue #24: [CORE] Proxy configuration module
**Labels:** `core`, `week-5`
**Priority:** P1

**Description:**
Support residential proxy configuration.

**Tasks:**
- [x] Environment variable support
- [x] Config file support
- [ ] Runtime configuration via bot
- [ ] Proxy status check

**Acceptance Criteria:**
- Proxy can be configured
- Traffic routes through proxy

---

### Issue #25: [UX] First-run setup wizard
**Labels:** `ux`, `week-5`
**Priority:** P1

**Description:**
Interactive setup for first-time users.

**Tasks:**
- [x] Token input prompts
- [x] Proxy configuration
- [x] Config file generation
- [ ] Validation feedback

**Acceptance Criteria:**
- Setup completes successfully
- Config is valid

---

## Week 6: Docs + Release (5 Issues)

### Issue #26: [DOCS] README + installation guide
**Labels:** `docs`, `week-6`
**Priority:** P0

**Description:**
Write comprehensive documentation.

**Tasks:**
- [x] README with quick start
- [ ] Detailed installation guide
- [ ] Troubleshooting section
- [ ] FAQ

**Acceptance Criteria:**
- New users can get started
- Common issues are addressed

---

### Issue #27: [DOCS] Proxy best practices (with affiliate links)
**Labels:** `docs`, `week-6`
**Priority:** P1

**Description:**
Guide for using residential proxies.

**Tasks:**
- [ ] Why proxies are needed
- [ ] Provider recommendations
- [ ] Configuration steps
- [ ] Troubleshooting

**Acceptance Criteria:**
- Users understand when to use proxy
- Links are properly embedded

---

### Issue #28: [DOCS] DigitalOcean deployment guide
**Labels:** `docs`, `week-6`
**Priority:** P1

**Description:**
Step-by-step DO deployment tutorial.

**Tasks:**
- [ ] One-click deploy setup
- [ ] Manual deployment steps
- [ ] Environment configuration
- [ ] Domain/SSL setup

**Acceptance Criteria:**
- Users can deploy to DO
- Affiliate link works

---

### Issue #29: [TEST] Unit tests + integration tests
**Labels:** `test`, `week-6`
**Priority:** P0

**Description:**
Comprehensive test coverage.

**Tasks:**
- [x] Test configuration
- [ ] Core module tests
- [ ] Adapter tests (mocked)
- [ ] Integration tests

**Acceptance Criteria:**
- Coverage > 70%
- All tests pass

---

### Issue #30: [RELEASE] PyPI + Docker Hub publishing
**Labels:** `release`, `week-6`
**Priority:** P0

**Description:**
Publish packages to registries.

**Tasks:**
- [ ] PyPI account setup
- [ ] Docker Hub account setup
- [ ] Version tagging
- [ ] Release notes

**Acceptance Criteria:**
- Package installable via pip
- Image pullable from Docker Hub

---

## Quick Create Commands

```bash
# Create all issues using GitHub CLI
gh issue create --title "[INFRA] Project structure initialization + Poetry config" --label "infrastructure,week-1" --body "..."
gh issue create --title "[INFRA] GitHub Actions CI/CD configuration" --label "infrastructure,week-1" --body "..."
# ... repeat for all 30 issues
```

## Labels to Create

```bash
gh label create "week-1" --color "0E8A16"
gh label create "week-2" --color "1D76DB"
gh label create "week-3" --color "5319E7"
gh label create "week-4" --color "FBCA04"
gh label create "week-5" --color "D93F0B"
gh label create "week-6" --color "B60205"
gh label create "infrastructure" --color "C5DEF5"
gh label create "core" --color "BFD4F2"
gh label create "adapter" --color "D4C5F9"
gh label create "render" --color "FEF2C0"
gh label create "docker" --color "F9D0C4"
gh label create "docs" --color "0075CA"
gh label create "test" --color "E99695"
gh label create "release" --color "006B75"
gh label create "telegram" --color "0088CC"
gh label create "dingtalk" --color "007AFF"
gh label create "opencode" --color "6E5494"
gh label create "ux" --color "FFC0CB"
```
