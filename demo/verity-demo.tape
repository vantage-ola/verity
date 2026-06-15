Output verity-demo.mp4

Set Shell "zsh"
Set FontSize 20
Set Width 1920
Set Height 1080
Set Theme "Catppuccin Mocha"
Set Padding 32
Set Framerate 30
Set TypingSpeed 45ms
Set WaitTimeout 30s

# ── hidden setup (not recorded) ───────────────────────────────────────────────
Hide
Type "export PS1='%% '"
Enter
Type "rm -rf /tmp/verity-demo"
Enter
Type "mkdir -p /tmp/verity-demo/agent-a/.verity /tmp/verity-demo/agent-a/tests /tmp/verity-demo/agent-a/reports /tmp/verity-demo/agent-b/.verity /tmp/verity-demo/agent-b/tests /tmp/verity-demo/keys"
Enter
Type "printf 'def test_charge():\n    assert True\n' > /tmp/verity-demo/agent-a/tests/test_payments.py"
Enter
Type "echo '{}' > /tmp/verity-demo/agent-a/reports/ci.json"
Enter
Type "printf 'def test_audit():\n    assert True\n' > /tmp/verity-demo/agent-b/tests/test_audit.py"
Enter
Type "verity keygen --key /tmp/verity-demo/keys/agent-a.key --force"
Enter
Sleep 3s
Show

# ── AGENT A — builds the proof chain ──────────────────────────────────────────
Type "cd /tmp/verity-demo/agent-a"
Enter
Sleep 500ms

Type "verity init --repo-id repo:payments-api"
Enter
Sleep 1.5s

Type "verity add feature feat:payments 'Payment processing'"
Enter
Sleep 700ms

Type "verity track feat:payments tests/test_payments.py"
Enter
Sleep 1.5s

Type "verity status"
Enter
Sleep 2.5s

Type "verity release 1.0.0"
Enter
Sleep 800ms

Type "verity push --upload-artifacts | tee /tmp/push-a1.txt"
Enter
Wait+Screen@30s /blob:/
Sleep 1.5s

Type "verity sign --key /tmp/verity-demo/keys/agent-a.key"
Enter
Sleep 1.5s

Type "verity push | tee /tmp/push-a2.txt"
Enter
Wait+Screen@30s /blob:/
Sleep 1s

Type "BLOB_A=$(awk '/^blob:/{print $2}' /tmp/push-a2.txt)"
Enter
Sleep 400ms

Type "echo 'handoff token:' $BLOB_A"
Enter
Sleep 3s

# ── AGENT B — verifies and extends ────────────────────────────────────────────
Type "clear"
Enter
Sleep 500ms

Type "cd /tmp/verity-demo/agent-b"
Enter
Sleep 400ms

Type "verity pull $BLOB_A"
Enter
Sleep 8s

Type "verity verify $BLOB_A"
Enter
Sleep 3.5s

Type "verity add feature feat:audit 'Audit logging'"
Enter
Sleep 700ms

Type "verity track feat:audit tests/test_audit.py"
Enter
Sleep 1.5s

Type "verity release 1.1.0"
Enter
Sleep 800ms

Type "verity push | tee /tmp/push-b.txt"
Enter
Wait+Screen@30s /blob:/
Sleep 1s

Type "BLOB_B=$(awk '/^blob:/{print $2}' /tmp/push-b.txt)"
Enter
Sleep 400ms

Type "echo 'new blob:' $BLOB_B"
Enter
Sleep 3s

# ── AGENT A — sees the full picture ───────────────────────────────────────────
Type "clear"
Enter
Sleep 500ms

Type "cd /tmp/verity-demo/agent-a"
Enter
Sleep 400ms

Type "verity pull $BLOB_B --force"
Enter
Sleep 8s

Type "verity status"
Enter
Sleep 4s
