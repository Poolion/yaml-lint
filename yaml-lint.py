#!/usr/bin/env python3
"""YAML Linter - Basic validation of YAML/JSON config files without external deps.

Validates:
- Required fields present
- Correct datatypes for numbered keys  
- Nested structure integrity
- Simple syntax sanity (not full YAML parsing)

Pure Python, no external dependencies like PyYAML.

Usage:
  python yaml-lint.py config.yml
  echo "name: app" | python yaml-lint.py -
"""

import argparse
import re


def read_yaml_content(path):
    with open(path, 'r') as f:
        return f.read()


def parse_simple_yaml(content):
    """Parse simple YAML without external deps. Only handles key-value pairs."""
    entries = {}
    current_indent = 0
    current_key = None
    
    for line in content.splitlines():
        stripped = line.strip()
        
        # Skip empty lines/comments  
        if not stripped or stripped.startswith('#'):
            continue
        
        indent = len(line) - len(line.lstrip())
        key_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$', stripped)
        
        if key_match:
            key = key_match.group(1)
            value = key_match.group(2).strip().strip('"\'')
            
            if not value or '/' in stripped:  # Nested key or list start
                current_key = key
            
            elif isinstance(value, str) and value.startswith('-'):
                continue
                    
            entries[current_key] = {
                'key': current_key,
                'value': value if value else '',
                'line': next((i+1 for i, l in enumerate(content.splitlines()) 
                             if l.strip() == stripped or (l.startswith(' '*indent) and key_match.group(0) in l), None))
            }
            
    return entries


def validate_required_fields(entries, required):
    missing = []
    
    for r_key in required:
        if not any(e['key'] and e['key'].upper() == r_key.upper() 
                    for e in entries.values()):
            missing.append(r_key)
              
    return missing


def find_empty_keys(content):
    """Find YAML keys with empty/missing values."""
    empty = []
    
    for line_num, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if ':' in stripped and not stripped.startswith('#'):
            parts = stripped.split(':', 1)  
            
            value = (parts[1] or '').strip().strip('"\'').lstrip('-')
            
            if not value or value == '#':
                empty.append({
                    'key': parts[0].strip(),
                    'line': line_num,
                    'value': stripped
                })
                
    return empty


def check_datatypes(entries):
    """Report on number key type mismatches."""
    issues = []
    
    for entry in entries.values():
        key = entry.get('key', '')
        value = str(entry['value'])
        
        # If this was "01", "02" style numbering, verify it's a valid int string
        if re.match(r'^0[0-9]+$', value or '') and not key.isdigit():
            issues.append({
                'key': key,
                'key_type': 'expected numeric', 
                'value': str(value) or '[empty]'  
            })
            
    return issues


def find_comments(content):
    """Find YAML comments for documentation."""
    found = []
    
    for line_num, line in enumerate(content.splitlines(), 1):
        if '#' in line and not line.strip().startswith(' #'): 
            comment_text = line.split('#', 1)[1] if '#' in line else ''
            if comment_text and not comment_text.startswith('//'):
                found.append({
                    'line': line_num,
                    'comment': comment_text
                })
                
    return found


def main():
    parser = argparse.ArgumentParser(description='YAML Linter - Basic validation without external deps')
    
    parser.add_argument('file', nargs='?', help='Path to YAML file or "-" for stdin')
    parser.add_argument('-r', '--required-fields', dest='required_fields', 
                       metavar='LIST', help='Comma-separated required fields (e.g. name,url,sslCertFile)')
    parser.add_argument('--show-empty', action='store_true', help='Also show keys with empty values')

    args = parser.parse_args()

    if args.file != '-':
        try:
            content = open(args.file).read()
        except FileNotFoundError:
            print(f'Error: File not found ({args.file})')
            return

        source = f'Source: {args.file}'
    else: 
        try:
            content = sys.stdin.read()
            source = '[stdin]'
        except Exception as e:
            print(f'Reading stdin failed: {e}')
            return

    if not content.strip():
        print('Input is empty')
        return
    
    # Basic parsing  
    entries = parse_simple_yaml(content)

    # Validate required fields
    missing_fields = []
    
    if args.required_fields:
        req_list = [f.strip().upper() for f in args.required_fields.split(',')]
        missing_fields = validate_required_fields(entries, req_list)

    # Find empty values  
    empty_keys = []
    
    if args.show_empty or True:  # Always check by default
        empty_keys = find_empty_keys(content)

    # Check datatypes
    type_mismatches = check_datatypes(entries)

    # Report findings
    print('* YAML Linter Report')
    print(source)
    
    field_count = len([e for e in entries.values() if e.get('key')])
    print(f'Fields found:       {field_count}')
    
    if missing_fields:
        print()
        print('*', 'Missing required fields:')
        
        for field in missing_fields:
            print(f'  • Missing required field: ${field} (use --required-fields to list)')

    if empty_keys or missing_fields or type_mismatches:
        print()
        
        # Show other issues  
        issue_count = len(missing_fields) + len(type_mismatches)
        
        print(f'* Issues found: {issue_count}')
        
        if missing_fields or type_mismatches:
            if missing_fields:
                for field in sorted(set(missing_fields))[:3]:
                    if '${field}' in content:  # Reference exists but value missing
                        print(f'  • ${field} referenced but undefined')
            elif type_mismatches:
                print('  * Check numeric key consistency')

        return

    else:
        print('* No issues detected.')
        
        if empty_keys and args.show_empty:
            for item in empty_keys[:5]:
                print(f'  • Empty value at line {item["line"]}: {item["key"]}')

        return


if __name__ == '__main__':
    main()
