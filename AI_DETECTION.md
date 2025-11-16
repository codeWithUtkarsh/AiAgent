# AI-Powered Package Manager Detection

## Overview

The AI Agent now features **intelligent, AI-powered package manager detection** using Claude to analyze repository structure and automatically identify the correct package manager and project type.

## Why AI Detection?

### Problems with Traditional Detection

**❌ Hardcoded Rules:**
- Limited to predefined file patterns
- Requires code changes for each new package manager
- Can't handle edge cases or non-standard setups
- Fails with complex monorepos

**❌ Not Scalable:**
```python
# Old approach - hardcoded
if file_exists("package.json"):
    return "npm"
elif file_exists("requirements.txt"):
    return "pip"
```

### Benefits of AI Detection

**✅ Intelligent Analysis:**
- Claude analyzes entire repository structure
- Understands context and project patterns
- Handles non-standard configurations
- Adapts to new package managers without code changes

**✅ Robust & Scalable:**
- Works with any technology stack
- Identifies multiple package managers in monorepos
- Provides confidence scores
- Explains reasoning

## How It Works

### 1. Repository Scanning

The AI detector scans the repository structure:

```python
{
  "root_files": ["package.json", "tsconfig.json", "README.md"],
  "directories": ["src", "node_modules", "dist"],
  "file_extensions": [".ts", ".json", ".md"],
  "dependency_files": ["package.json", "package-lock.json"]
}
```

### 2. AI Analysis

Claude analyzes the structure with this prompt:

```
Analyze this repository structure and identify the package manager and project type.

Repository Structure:
- Root files: package.json, tsconfig.json, README.md, ...
- Directories: src, node_modules, dist, ...
- File extensions: .ts, .json, .md, ...
- Dependency files found: package.json, package-lock.json

Determine:
1. The PRIMARY package manager
2. Your confidence level
3. If it's a monorepo
4. The programming language/framework
```

### 3. Structured Response

Claude provides structured output:

```
PRIMARY_PACKAGE_MANAGER: npm
CONFIDENCE: high
LANGUAGE: TypeScript
FRAMEWORK: Next.js
IS_MONOREPO: no
REASONING: Found package.json with package-lock.json, TypeScript config,
and Next.js-specific files. Clear npm project structure.
```

### 4. Verification

The detected package manager is verified:

```python
# AI says "npm" → create NpmPackageManager instance
pm_instance = NpmPackageManager(repo_path)

# Verify it actually works
if pm_instance.detect():
    return pm_instance  # ✓ Verified
else:
    return fallback_detection()  # ✗ Try fallback
```

## Detection Modes

### Mode 1: AI-Powered (Recommended)

**When:** Anthropic API key configured
**How:** Claude analyzes repository structure
**Fallback:** Rule-based detection if AI fails

```python
# Automatically uses AI when API key available
package_manager = PackageManagerDetector.detect(
    repo_path,
    anthropic_api_key="sk-ant-..."
)
```

### Mode 2: Rule-Based (Fallback)

**When:** No API key or AI detection fails
**How:** Hardcoded file pattern matching
**Limitations:** Only detects npm, pip, cargo

```python
# Falls back to rules if no API key
package_manager = PackageManagerDetector.detect(repo_path)
```

## Supported Package Managers

### Currently Implemented

Via AI detection:
- ✅ **npm** (Node.js)
- ✅ **yarn** (Node.js)
- ✅ **pnpm** (Node.js)
- ✅ **pip** (Python)
- ✅ **poetry** (Python)
- ✅ **pipenv** (Python)
- ✅ **cargo** (Rust)

### AI Can Detect (Implementation Needed)

Claude can identify these, but implementations need to be added:
- 🔜 **maven** (Java)
- 🔜 **gradle** (Java/Kotlin)
- 🔜 **go modules** (Go)
- 🔜 **composer** (PHP)
- 🔜 **bundler** (Ruby)
- 🔜 **mix** (Elixir)
- 🔜 **pub** (Dart)
- 🔜 **sbt** (Scala)

### Adding New Package Managers

**Old Way (Hardcoded):**
```python
# 1. Create new class
class MavenPackageManager(BasePackageManager):
    def detect(self):
        return self.file_exists("pom.xml")
    # ... more code ...

# 2. Register in detector
PACKAGE_MANAGERS = [
    NpmPackageManager,
    PipPackageManager,
    MavenPackageManager,  # ← Add here
]
```

**New Way (AI-Powered):**
```python
# 1. Just add to mapping
PACKAGE_MANAGER_MAP = {
    'maven': MavenPackageManager,  # ← That's it!
    'mvn': MavenPackageManager,
}

# AI automatically detects Maven projects
# No need to update detection logic
```

## Configuration

### Enable AI Detection

Set Anthropic API key in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### Disable AI Detection

Remove or comment out the API key:

```env
# ANTHROPIC_API_KEY=
```

The system automatically falls back to rule-based detection.

## Logs & Debugging

### AI Detection Logs

```
[INFO] Detecting package manager in /path/to/repo
[INFO] Attempting AI-powered package manager detection
[INFO] Scanned repository: 25 files, 8 directories
[INFO] Found dependency files: ['package.json', 'package-lock.json']
[INFO] Analyzing repository with AI...
[INFO] AI Analysis Response:
PRIMARY_PACKAGE_MANAGER: npm
CONFIDENCE: high
LANGUAGE: JavaScript
[INFO] AI suggested package manager: npm
[INFO] ✓ Verified AI suggestion: npm
[INFO] ✓ AI detected package manager: npm
```

### Fallback Detection Logs

```
[INFO] Detecting package manager in /path/to/repo
[WARNING] AI detection not available, falling back to rule-based detection
[INFO] Using rule-based package manager detection
[INFO] ✓ Rule-based detection found: npm
```

## Monorepo Support

AI can detect monorepos with multiple package managers:

```
PRIMARY_PACKAGE_MANAGER: npm
IS_MONOREPO: yes
REASONING: Found both npm (frontend/) and cargo (backend/) package managers
```

```python
# Get all package managers in monorepo
managers = PackageManagerDetector.get_all_package_managers(
    repo_path,
    anthropic_api_key="sk-ant-..."
)
# Returns: [NpmPackageManager, CargoPackageManager]
```

## Error Handling

### AI Detection Fails

1. Logs error details
2. Falls back to rule-based detection
3. Continues normal flow

### No Package Manager Detected

```python
package_manager = PackageManagerDetector.detect(repo_path)
if not package_manager:
    raise Exception("No supported package manager detected")
```

## Performance

- **AI Detection:** ~2-5 seconds (single API call)
- **Rule-based:** <100ms (file system checks)
- **Total Impact:** Minimal (AI runs once per job)

## Cost Considerations

- **Tokens per detection:** ~100-200 tokens (~$0.001)
- **Frequency:** Once per repository analysis
- **Monthly cost:** Negligible for typical usage

## Future Enhancements

1. **Cache AI Results:** Store detection results to avoid repeat API calls
2. **Batch Detection:** Analyze multiple repos in single API call
3. **Custom Prompts:** Allow users to customize detection prompts
4. **Learning:** Track detection accuracy and improve prompts
5. **Local Models:** Support local LLMs for offline detection

## Architecture

```
┌─────────────────────────────────────┐
│   PackageManagerDetector            │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Try AI Detection            │  │
│  │  ↓                            │  │
│  │  AIPackageManagerDetector    │  │
│  │    - Scan repository         │  │
│  │    - Call Claude API         │  │
│  │    - Parse response          │  │
│  │  ↓                            │  │
│  │  Create & Verify PM instance │  │
│  └──────────────────────────────┘  │
│          ↓ (if fails)               │
│  ┌──────────────────────────────┐  │
│  │  Fallback to Rules           │  │
│  │    - Check file patterns     │  │
│  │    - Return first match      │  │
│  └──────────────────────────────┘  │
│          ↓                          │
│  PackageManager Instance            │
└─────────────────────────────────────┘
```

## API Reference

### AIPackageManagerDetector

```python
detector = AIPackageManagerDetector(anthropic_api_key)

# Scan repository
structure = detector.scan_repository_structure(repo_path)

# Detect with AI
result = await detector.detect_with_ai(repo_path)
# Returns: {'package_manager': 'npm', 'confidence': 'high', ...}
```

### PackageManagerDetector

```python
# AI-powered detection (recommended)
pm = PackageManagerDetector.detect(
    repo_path,
    anthropic_api_key="sk-ant-..."
)

# Rule-based detection (fallback)
pm = PackageManagerDetector.detect(repo_path)

# Monorepo support
managers = PackageManagerDetector.get_all_package_managers(
    repo_path,
    anthropic_api_key="sk-ant-..."
)
```

## Examples

### Example 1: Next.js Project

**Repository Structure:**
```
├── package.json
├── package-lock.json
├── next.config.js
├── tsconfig.json
└── pages/
```

**AI Detection:**
```
PRIMARY_PACKAGE_MANAGER: npm
CONFIDENCE: high
LANGUAGE: TypeScript
FRAMEWORK: Next.js
REASONING: Next.js project with npm package manager
```

### Example 2: Python Poetry Project

**Repository Structure:**
```
├── pyproject.toml
├── poetry.lock
├── setup.py
└── src/
```

**AI Detection:**
```
PRIMARY_PACKAGE_MANAGER: poetry
CONFIDENCE: high
LANGUAGE: Python
REASONING: Found pyproject.toml and poetry.lock
```

### Example 3: Rust Cargo Project

**Repository Structure:**
```
├── Cargo.toml
├── Cargo.lock
└── src/
    └── main.rs
```

**AI Detection:**
```
PRIMARY_PACKAGE_MANAGER: cargo
CONFIDENCE: high
LANGUAGE: Rust
REASONING: Cargo project with Rust source files
```

## Comparison

| Feature | Rule-Based | AI-Powered |
|---------|-----------|------------|
| Speed | ⚡ Fast (<100ms) | 🐢 Slower (~3s) |
| Accuracy | ✓ Good for known | ✓✓ Excellent |
| Scalability | ❌ Limited | ✅ Unlimited |
| Edge Cases | ❌ Poor | ✅ Excellent |
| New PM Support | ❌ Code change | ✅ Auto-detect |
| Monorepo | ⚠️ Partial | ✅ Full support |
| Offline | ✅ Yes | ❌ Needs API |
| Cost | Free | ~$0.001/detect |

## Best Practices

1. **Always enable AI detection** for production use
2. **Monitor API usage** to manage costs
3. **Review AI suggestions** in logs for accuracy
4. **Report false detections** to improve prompts
5. **Keep fallback enabled** for reliability

## Troubleshooting

### AI Not Being Used

Check logs for:
```
[WARNING] Anthropic API key not configured. AI features will be disabled.
```

Solution: Set `ANTHROPIC_API_KEY` in `.env`

### AI Detection Failing

Check logs for:
```
[ERROR] Error in AI detection: <error details>
[INFO] Using rule-based package manager detection
```

Solution: Verify API key is valid and has credits

### Wrong Package Manager Detected

Check logs for AI reasoning:
```
REASONING: <why AI chose this PM>
```

Solution: Review repository structure, may need implementation for detected PM

---

**Built with**: Claude 3.5 Sonnet for intelligent repository analysis
