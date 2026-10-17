#!/bin/sh
# Install a local pre-commit hook that blocks API-key-shaped strings (hooks are not tracked by Git).
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
hook="$repo/.git/hooks/pre-commit"
marker='# opencode-haiku secret scan'
if [ -e "$hook" ] && ! grep -q "$marker" "$hook"; then
  echo "A different pre-commit hook exists at $hook; not overwriting it." >&2; exit 1
fi
cat > "$hook" <<HOOK
#!/bin/sh
$marker
exec python3 "\$(git rev-parse --show-toplevel)/tools/secrets/scan_secrets.py" --staged
HOOK
chmod +x "$hook"
echo "Installed $hook"
