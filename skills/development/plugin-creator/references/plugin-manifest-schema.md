# Plugin Manifest Schema

The plugin manifest (`plugin.json`) is located in the `.claude-plugin/` directory and defines the plugin's metadata and configuration.

## Location

```
my-plugin/
└── .claude-plugin/
    └── plugin.json
```

## Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique plugin identifier. Lowercase, alphanumeric, hyphens allowed. |
| `version` | string | Semantic version (e.g., "1.0.0", "2.1.3-beta") |
| `description` | string | Brief description of what the plugin does |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Plugin author name or organization |
| `homepage` | string | URL to plugin documentation or homepage |
| `repository` | string | URL to source code repository |
| `license` | string | SPDX license identifier (e.g., "MIT", "Apache-2.0") |
| `keywords` | string[] | Keywords for plugin discovery |
| `dependencies` | object | Required external tools or services |

## Examples

### Minimal Manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "A simple Claude Code plugin"
}
```

### Full Manifest

```json
{
  "name": "code-review-toolkit",
  "version": "2.1.0",
  "description": "Comprehensive code review tools with security scanning and style checking",
  "author": "Acme Corp",
  "homepage": "https://example.com/code-review-toolkit",
  "repository": "https://github.com/acme/code-review-toolkit",
  "license": "MIT",
  "keywords": [
    "code-review",
    "security",
    "linting",
    "best-practices"
  ],
  "dependencies": {
    "node": ">=18.0.0",
    "python": ">=3.10"
  }
}
```

## Name Conventions

- Must start with a lowercase letter
- Can contain lowercase letters, numbers, and hyphens
- Cannot start or end with a hyphen
- Maximum 64 characters

**Valid names:**
- `my-plugin`
- `code-review-toolkit`
- `ai-helper2`

**Invalid names:**
- `My-Plugin` (uppercase)
- `-my-plugin` (starts with hyphen)
- `my_plugin` (underscores not allowed)

## Version Format

Follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)
- **PRERELEASE**: Optional pre-release identifier

**Examples:**
- `1.0.0` - Initial release
- `1.1.0` - New feature
- `1.1.1` - Bug fix
- `2.0.0-beta` - Major version pre-release
- `2.0.0-rc.1` - Release candidate

## Validation

The manifest is validated when:
1. Loading the plugin (`claude --plugin-dir`)
2. Running `validate_plugin.py`
3. Packaging for distribution

Validation checks:
- JSON syntax
- Required fields present
- Name format
- Version format (warning if invalid)
