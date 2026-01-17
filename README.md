# Detective Evidence System - Snowflake Setup

## 🚀 Quick Start (Works for Everyone!)

```bash
# 1. Install dependencies
npm install

# 2. Start the server (no credentials needed!)
npm start

# 3. Open the app
open index.html
```

**That's it!** The system runs in **LOCAL MODE** by default. No Snowflake account required!

---

## 🎯 Two Operating Modes

### 📝 Local Mode (Default - No Setup)
- ✅ Works immediately for all team members
- ✅ No Snowflake credentials required
- ✅ Evidence stored in local files
- ✅ Perfect for development and testing

### ❄️ Snowflake Mode (Optional - Per Person)
- 🔐 Each person uses their own Snowflake account
- ☁️ Evidence stored in Snowflake database
- 🔄 Seamlessly falls back to local mode if connection fails

---

## 🔧 Enable Snowflake (Optional)

**Only if you have a Snowflake account:**

### 1. Add your credentials to `.env`

The `.env` file already exists. Just fill in your credentials:

```env
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USERNAME=your_username
SNOWFLAKE_PASSWORD=your_password
```

**Finding your account identifier:**
- Log into Snowflake
- Look at the URL: `https://[ACCOUNT].snowflakecomputing.com`
- Example: `ab12345.us-east-1` or `orgname-accountname`

### 2. Restart the server

```bash
npm start
```

You'll see: ✅ SNOWFLAKE MODE: Evidence will be stored in Snowflake

---

## 🤝 Team Collaboration

### How It Works:
1. **.env is NOT committed** to git (protected by .gitignore)
2. Each person configures their own `.env` locally
3. Some team members use Snowflake, others use local mode
4. Everyone commits code normally

### What's Shared:
- ✅ `.env.example` - Template file (no secrets)
- ✅ Source code - All `.js`, `.html`, `.css` files
- ✅ `package.json` - Dependencies
- ✅ Documentation

### What's Private:
- 🔒 `.env` - Your personal credentials (NEVER commit!)
- 🔒 `node_modules/` - Dependencies (auto-generated)
- 🔒 `uploads/` - Uploaded files

---

## 📊 When to Use Each Mode

### Use Local Mode When:
- 🧪 Testing and development
- 🎓 You don't have Snowflake access
- ⚡ You want quick setup
- 🔌 Working offline

### Use Snowflake Mode When:
- ☁️ You need cloud storage
- 🔍 You want to query data in SQL
- 👥 Sharing data with your Snowflake team
- 📈 Production deployment

---

## 🛡️ Security Best Practices

### ✅ DO:
- Keep your `.env` file LOCAL
- Use your own Snowflake credentials
- Commit `.env.example` (no secrets)
- Share this README with teammates

### ❌ DON'T:
- **Never commit `.env`** to git
- Don't share passwords in chat/email
- Don't hardcode credentials in code
- Don't use someone else's account

---

## 🧪 Testing Both Modes

### Test Local Mode:
```bash
# Clear credentials in .env
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USERNAME=
SNOWFLAKE_PASSWORD=

# Restart
npm start
```

### Test Snowflake Mode:
```bash
# Add credentials in .env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USERNAME=your_username
SNOWFLAKE_PASSWORD=your_password

# Restart
npm start
```

---

## 📋 Snowflake Table Structure

When using Snowflake mode, this table is auto-created:

```sql
CREATE TABLE FORENSIC_EVIDENCE (
    EVIDENCE_ID NUMBER AUTOINCREMENT PRIMARY KEY,
    CASE_NUMBER VARCHAR(100),
    DESCRIPTION TEXT,
    COLLECTED_BY VARCHAR(200),
    DATE_COLLECTED DATE,
    TIME_COLLECTED TIME,
    LOCATION VARCHAR(500),
    FILE_NAMES TEXT,
    FILE_COUNT NUMBER,
    SUBMITTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    METADATA VARIANT
)
```

---

## 🆘 Troubleshooting

**"I don't have Snowflake credentials"**
- No problem! Just use local mode (default)

**"Server won't start"**
- Make sure port 3000 isn't in use
- Run `npm install` first

**"Snowflake connection failed"**
- Server automatically falls back to local mode
- Check your credentials in `.env`
- Verify your Snowflake account is active

**"My teammate can't run the app"**
- Make sure they run `npm install`
- They don't need Snowflake credentials
- App works in local mode by default

---

## 📚 Additional Documentation

- **TEAM_SETUP.md** - Detailed team collaboration guide
- **.env.example** - Configuration template with comments

Need help? The server will show clear messages about which mode it's running in!
