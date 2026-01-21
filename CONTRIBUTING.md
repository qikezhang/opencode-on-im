# Contributing to OpenCode on IM

Thank you for considering contributing to OpenCode on IM!

## Prerequisites

- Node.js 20+
- npm
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenCode installed locally (for plugin testing)

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/qikezhang/opencode-on-im.git
   cd opencode-on-im
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Build the project**

   ```bash
   npm run build
   ```

4. **Type check**

   ```bash
   npm run typecheck
   ```

## Project Structure

```
opencode-on-im/
├── src-ts/
│   ├── index.ts          # Plugin entry point, exports tools
│   ├── state.ts          # State management (bindings, codes, etc.)
│   ├── standalone.ts     # Standalone mode for testing
│   └── telegram/
│       └── bot.ts        # Grammy-based Telegram bot
├── test-env/             # Docker test environment
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── test-env.sh
├── dist/                 # Compiled output (gitignored)
├── package.json
└── tsconfig.json
```

## Testing

### Unit Testing

```bash
npm run typecheck
npm test
```

### Docker Test Environment

An isolated Docker environment is provided for integration testing:

```bash
cd test-env
./test-env.sh start   # Build and start container
./test-env.sh shell   # Open shell in container
./test-env.sh stop    # Stop container
./test-env.sh clean   # Remove all test data
```

### Standalone Mode

Test the bot without OpenCode plugin context:

```bash
export TELEGRAM_TOKEN=your_token
npm run build
node dist/standalone.js --test
```

## Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run `npm run typecheck` to ensure no type errors
4. Commit with clear messages following conventional commits
5. Push and open a Pull Request

## Code Style

- **TypeScript strict mode** - No `any` types, proper type annotations
- **No type suppressions** - Avoid `@ts-ignore`, `@ts-expect-error`, `as any`
- **Functional patterns** - Prefer pure functions where possible
- **Clear naming** - Descriptive variable and function names
- **Error handling** - Always handle errors appropriately

## Pull Request Guidelines

- Keep PRs focused on a single change
- Include a clear description of what and why
- Reference any related issues
- Ensure all checks pass before requesting review

## Questions?

Open an issue for discussion before making large changes.
