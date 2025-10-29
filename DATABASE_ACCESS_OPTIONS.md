# Database Access Options

**Current Status**: Database has **private IP only** (10.240.0.3)
**Your Public IP**: 162.239.0.122

---

## 🎯 What We're Doing

Enabling public IP access with your IP allowlisted so migrations can run from this machine.

---

## ✅ Option 1: Add Public IP (Currently Executing)

### Command Running:
```bash
gcloud sql instances patch dev-vividly-db \
  --project=vividly-dev-rich \
  --assign-ip \
  --authorized-networks=162.239.0.122/32
```

### What This Does:
- ✅ Adds a public IP to your database instance
- ✅ Restricts access to ONLY your IP (162.239.0.122)
- ✅ Keeps private IP (10.240.0.3) for internal access
- ✅ Still secure - IP allowlist prevents unauthorized access
- ✅ Takes ~2-3 minutes to complete

### After This Completes:
1. Database will have both private IP (10.240.0.3) AND public IP
2. Only your current IP can connect via public IP
3. I can run migrations directly from this machine
4. No need for Cloud Shell

---

## 📊 Comparison of Access Methods

| Method | Pros | Cons | Time to Setup |
|--------|------|------|---------------|
| **Public IP + Allowlist** | ✅ Direct access<br>✅ Fast migrations<br>✅ Still secure | ⚠️ Needs IP update if you move | 3 minutes |
| **Cloud Shell** | ✅ Always works<br>✅ Built-in VPC access | ⏱️ Manual file upload<br>⏱️ Extra steps | 5 minutes |
| **Cloud SQL Proxy** | ✅ Encrypted tunnel<br>✅ No public IP needed | 🔴 Complex setup<br>🔴 Didn't work earlier | 10+ minutes |

---

## 🔐 Security Notes

### Current Setup is Secure:
- ✅ Only your IP (162.239.0.122) can connect
- ✅ Still requires password authentication
- ✅ SSL/TLS encryption enforced
- ✅ Private IP still available for internal GCP services
- ✅ No open access to internet

### IP Allowlist Restrictions:
```
/32 = Single IP address (most restrictive)
162.239.0.122/32 = ONLY this exact IP
```

---

## 🔄 If Your IP Changes

If you connect from a different location/network:

```bash
# Get your new IP
curl https://api.ipify.org

# Add the new IP
gcloud sql instances patch dev-vividly-db \
  --project=vividly-dev-rich \
  --authorized-networks=OLD_IP/32,NEW_IP/32
```

---

## 🎬 What Happens Next

### 1. Wait for Database Update (2-3 minutes)
The `gcloud sql instances patch` command is running in background.

### 2. Get Public IP Address
Once update completes:
```bash
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(ipAddresses[?type:PUBLIC].ipAddress)"
```

### 3. Test Connection
```bash
psql -h PUBLIC_IP -U vividly -d vividly -c "SELECT version();"
```

### 4. Run Migrations
I'll run all three migrations directly:
- Feature Flags
- Request Tracking
- Phase 2 Indexes

---

## 🚨 Troubleshooting

### Error: "Connection refused"
**Cause**: Database update still in progress
**Solution**: Wait 1-2 more minutes, then retry

### Error: "Connection timed out"
**Cause**: Your IP changed or firewall blocking
**Solution**:
```bash
# Verify your current IP
curl https://api.ipify.org

# Update authorized networks if IP changed
gcloud sql instances patch dev-vividly-db \
  --authorized-networks=NEW_IP/32
```

### Error: "SSL connection required"
**Cause**: Database requires SSL
**Solution**: Add `sslmode=require` to connection:
```bash
psql "host=PUBLIC_IP user=vividly dbname=vividly sslmode=require"
```

---

## 🔄 Alternative: Keep Private IP Only

If you prefer to keep database private-only:

### Use Cloud Shell Instead:
1. Open: https://console.cloud.google.com/?cloudshell=true
2. Upload migration files
3. Run: `bash run_all_migrations_cloudshell.sh`

### Revert to Private-Only:
```bash
# Remove public IP (keep only private)
gcloud sql instances patch dev-vividly-db \
  --project=vividly-dev-rich \
  --no-assign-ip
```

---

## 📈 Best Practices

### For Development:
✅ **Public IP + Your IP Allowlisted** (what we're doing)
- Fast iteration
- Direct access
- Still secure

### For Production:
✅ **Private IP Only**
- Maximum security
- Use Cloud SQL Proxy from application servers
- No public internet exposure

---

## ⏱️ Current Status

Checking database update status...
