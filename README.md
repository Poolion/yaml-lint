# YAML Linter - Basic validation without external dependencies

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

Validate YAML/JSON config files for required fields, empty values, and basic structure without PyYAML or other external dependencies.

## Features

- Check for missing required fields (`--required-fields` flag)
- Detect keys with empty/undefined values (`--show-empty`)  
- Validate numbered key consistency (numeric vs non-numeric)
- Find YAML comments for documentation tracking
- Fast, zero-dependency Python implementation

## Installation

Add to your PATH anywhere:

```bash
cp ~/env-checker/yaml-lint.py /usr/local/bin/
yaml-lint.sh config.yml      # Validate config file  
yaml-lint.sh - < script       # Pipe input for validation
```

Or install directly from source:

```bash
git clone https://github.com/Poolion/env-checker.git
cd env-checker
pip install .      # Optional: if you want a package
python yaml-lint.sh config.yml   # Use the script file  
```

## Usage Examples

### Validate Required Fields  

Specify which fields must be present in your YAML:

```bash
python yaml-lint.py config.yml --required-fields name,url,sslCertFile
# or using flags directly:
yaml-lint.sh myconfig.yml -r "name,url,version"
```

**Example usage:**

```bash
$ python yaml-lint.py myapp/config.yml

* YAML Linter Report  
Source: myapp/config.yml  
Fields found:       12  

* No issues detected.
```

With missing required fields:

```python
python yaml-lint.sh config.yml --required-fields name,url,version  
# Missing required field: VERSION (no reference in file)
Missing required field: SSL_CERT_FILE
```

### Show Empty Values

Find keys with empty or undefined values to catch common config mistakes:

```bash
python yaml-lint.py -u config.yml --show-empty

* YAML Linter Report
Source: config.yml  
Fields found:       8  

* Issues found: 2 
• KeyError at line 5: DATABASE_URL
Empty value found: API_KEY (empty on line 10)
```

### From Stdin for Pipelines

Pipe content for validation in CI workflows:

```bash
cat my_config.yml | python yaml-lint.sh -  
# or  
echo "name: MyApp" > temp.txt && python yaml-lint.py < temp.txt
```

Useful for validating generated configs, templates, or documentation examples before committing.

## Command Line Options

| Option               | Description                                      |
|----------------------|--------------------------------------------------|
| `'`file``'           | Path to YAML file (or `-` for stdin)            |
| `--required-fields`  | Comma-separated list of fields that must exist  |
| `[--show-empty]`     | Show keys with empty/undefined values           |

**Full help:**

```bash
python3 env-checker/yaml-lint.py --help  
# Usage: python yaml-lint.py [OPTIONS] [file]
```

**Examples:**

```bash
yaml-lint.sh config.yml                                    # Basic validation
yaml-lint.sh app.json -r "version,author,built"             # Enforce 3 fields 
yaml-lint.sh < myconfig.yaml --required-fields name,url     # Stdin with requirements  
```

## Configuration Examples

A typical deployment config with validation:

```bash
# production.yml
# Usage: python yaml-lint.sh production.yml -r "apiVersion,namespace,replicas"

apiVersion: v2
name: MyApp
version: 1.0.0                    # Required field  
sslCertFile: /etc/ssl/certs/myapp.crt
# Additional configs...
```

Run this to validate before deployment pipelines:

```python
python yaml-lint.sh app/configs/production.yml -r "apiVersion,namespace,replicas,loggingLevel"
# Missing required field: LOGGING_LEVEL
```

Or with empty values:

```python
$ python3 env-checker/yaml-lint.py deploy.sh --show-empty  

* YAML Linter Report  
Source: deploy.sh  
Fields found:       14  

* Issues found: 2 
• Empty value at line 7: DATABASE_URL
Empty key found: API_KEY (empty on line

```

## How to Extend This Tool

Add custom type checks or new validation rules. The code is intentionally minimal!

Example: Add logging level hints

```python
def find_invalid_log_level(content): 
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NOTSET']  
    for line in content.splitlines():
        if '-log-level' in line and '=' in line:
            value = line.split('=', 1)[1].strip('"\'')
            
            if not any(level.upper() == value.upper() 
                      for level in levels):
                print(f'* Invalid log level {value}')
                
    return False

# Usage after parsing:  
if find_invalid_log_level(content):
    sys.exit(1)
```

## Integration Examples

### .github/workflows/build-and-validate.yml  

Validate configs before building Docker images:

```yaml
# Build step: validate configurations first  steps:
  - name: Check YAML configs
    run: python yaml-lint.sh app/configs/*.json -r "name,url,version" || exit 1
  
  - name: Build Docker image  
    uses: docker/build-push-action@v3
    
- name: Run tests    
  run: npm test
```

### Makefile linting target  

Include in your project's validation phase:

```python
.PHONY: validate-lint-checks  
validate-lint-checks:
        @echo "Validating YAML configs..." 
        for config in app/configs/*.json; do \
            python yaml-lint.sh $$config -r $(REQUIRED_FIELDS) || exit 1; 
        done
        
build: validate-lint-checks    
        make build-docker-image
```

### Script validation step  

Verify shell scripts before deployment:

```python
#!/bin/bash
# validate-deploy.sh
  
check_yaml() {  
    python yaml-lint.py "$@" -r "name,url" 
}

check_json() {  
    # Simple JSON validation without jq dep  
    if ! python3 json-validator.sh "$@"; then exit 1; fi  
}

validate-configs() {
    for f in configs/*.json configs/*.yml; do
        if [ -f "$f" ]; then
            check_yaml "$f" || echo "Validation failed for $$f"; exit 1;  
        fi 
    done
    
    cd scripts && bashcheck.sh * || (echo "Shell script failed"; exit 1); cd ..
}

validate-configs > /tmp/config-validation.log  
```

## Limitations to Know

Env Checker focuses on basic validation rather than comprehensive parsing:

- **No full YAML grammar** — Only handles simple key-value pairs (no anchors, complex nesting)  
- **Basic syntax** — Doesn't validate anchors, aliases, or multi-line strings fully 
- **Fast but limited** — Prioritizes zero-dependency speed over deep analysis  

For advanced use cases:

```bash
# Install PyYAML for deep validation if needed
pip install pyyaml
python yaml-deep-analyze.sh config.yml --strict    # Optional advanced version  
```

But for quick CI checks, documentation review, or template validation—Env Checker is fast and lightweight.

## Output Differences

| Scenario | Env Checker (`-r` flag) | PyYAML deep check |
|---|-------------------------|------------------------------------|
| Empty values | Shows which keys are undefined | Validates entire structure  |
| Required fields | Lists missing with line refs | Fails if field type mismatch |  
| Comments | Shows for documentation | May be stripped or ignored  |

For most CI/CD validation tasks—Env Checker's basic approach is sufficient without overhead.

## When to Use This Tool

Validate configs in these scenarios where PyYAML might be overkill:
- **Quick CI checks** — Fast boolean validation before building  
- **Documentation snippets** — Validate examples in docs don't break  
- **Template generation** — Ensure generated configs meet requirements  
- **Configuration auditing** — Check for missing required fields in production  |

Env Checker is your lightweight validation companion—add it to your Python toolkit for rapid, dependency-free config verification.

## Conclusion

YAML Linter provides fast, zero-dependencies YAML/JSON validation for common cases. Detects missing required fields and empty values without installing PyYAML or other packages. Perfect for CI/CD pipelines that need quick validation before build steps, or documentation maintainers who want to ensure config examples are valid.

For advanced deep syntax analysis (anchors, complex nesting), install PyYAML separately—but for standard field checks, this lightweight tool is what most projects need without overhead.

**Project:** https://github.com/Poolion/env-checker

If you find this useful, you can support development: https://www.buymeacoffee.com/poolion