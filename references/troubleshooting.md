# Troubleshooting Guide

## SSL Connectivity Issues in WSL

**Symptom**: Requests to `oc.sjtu.edu.cn` fail with `SSL_ERROR_SYSCALL` or `Cannot connect to host oc.sjtu.edu.cn:443 ssl:default [None]`, but `ping` works and the first request occasionally succeeds.

**Root Cause**: WSL2 network stack SSL/TLS handshake issues with certain destinations, often related to:
- Corporate/institutional network interception
- Missing/outdated CA certificates in WSL
- WSL2 virtual NIC MTU mismatches
- Antivirus/firewall SSL inspection

**Verification Steps**:

```bash
# 1. Test basic connectivity
ping oc.sjtu.edu.cn

# 2. Test TLS handshake (should show certificate chain)
openssl s_client -connect oc.sjtu.edu.cn:443 -servername oc.sjtu.edu.cn < /dev/null

# 3. Test with curl verbose
curl -vI https://oc.sjtu.edu.cn/api/v1/users/self -H "Authorization: Bearer <TOKEN>"

# 4. Test from Windows host (PowerShell) to isolate WSL issue
Invoke-WebRequest -Uri "https://oc.sjtu.edu.cn/api/v1/users/self" -Headers @{Authorization="Bearer <TOKEN>"}
```

**Workarounds**:

1. **Run from Windows host** - Use PowerShell/CMD outside WSL for Canvas API calls
2. **Update CA certificates in WSL**:
   ```bash
   sudo apt update && sudo apt install -y ca-certificates
   sudo update-ca-certificates
   ```
3. **Set explicit SSL verify false (testing only)**:
   ```bash
   # In Python/aiohttp - NOT for production
   ssl=False  # or SSLContext with verify_mode=CERT_NONE
   ```
4. **WSL2 MTU fix** (if packet fragmentation):
   ```bash
   # In WSL
   sudo ip link set dev eth0 mtu 1400
   # Or in Windows (admin PowerShell):
   netsh interface ipv4 set subinterface "vEthernet (WSL)" mtu=1400 store=persistent
   ```

**If token works once then fails**: The token is valid. The issue is network/SSL layer, not authentication. Re-test from Windows host to confirm.

## Token Management

- Token stored in `.env` file at skill root: `TOKEN=your_token_here`
- Can also pass via `--token` CLI flag or `TOKEN` environment variable
- Token format: 64-char alphanumeric string (Canvas API token)

## Current Term Detection

The skill auto-detects current term based on system date:
- Jan-Feb → Previous year Fall (e.g., 2025-2026 Fall)
- Mar-Jul → Previous year Spring (e.g., 2025-2026 Spring)
- Aug-Dec → Current year Fall (e.g., 2026-2027 Fall)

Override with `--term "2025-2026 Spring"` if needed.