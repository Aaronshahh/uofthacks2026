require('dotenv').config();
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const snowflake = require('snowflake-sdk');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.')); // Serve frontend files

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadDir = './uploads';
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir);
        }
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage });

// Snowflake connection configuration
// Supports multiple auth methods: password, key-pair, OAuth, SSO
function getSnowflakeConfig() {
    // Check if Snowflake is configured
    if (!process.env.SNOWFLAKE_ACCOUNT || !process.env.SNOWFLAKE_USERNAME) {
        console.warn('⚠️  Snowflake not configured. Evidence will be stored locally only.');
        return null;
    }

    const config = {
        account: process.env.SNOWFLAKE_ACCOUNT,
        username: process.env.SNOWFLAKE_USERNAME,
        database: process.env.SNOWFLAKE_DATABASE || 'EVIDENCE_DB',
        schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC',
        warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
        role: process.env.SNOWFLAKE_ROLE || 'ACCOUNTADMIN'
    };

    // Support different authentication methods
    if (process.env.SNOWFLAKE_PASSWORD) {
        config.password = process.env.SNOWFLAKE_PASSWORD;
    } else if (process.env.SNOWFLAKE_PRIVATE_KEY_PATH) {
        // Key-pair authentication (more secure for shared projects)
        const privateKeyPath = process.env.SNOWFLAKE_PRIVATE_KEY_PATH;
        if (fs.existsSync(privateKeyPath)) {
            config.privateKey = fs.readFileSync(privateKeyPath, 'utf8');
            if (process.env.SNOWFLAKE_PRIVATE_KEY_PASS) {
                config.privateKeyPass = process.env.SNOWFLAKE_PRIVATE_KEY_PASS;
            }
        }
    } else if (process.env.SNOWFLAKE_AUTHENTICATOR) {
        // OAuth or SSO authentication
        config.authenticator = process.env.SNOWFLAKE_AUTHENTICATOR;
        if (process.env.SNOWFLAKE_TOKEN) {
            config.token = process.env.SNOWFLAKE_TOKEN;
        }
    }

    return config;
}

// Create Snowflake connection
function createSnowflakeConnection() {
    return new Promise((resolve, reject) => {
        const config = getSnowflakeConfig();
        if (!config) {
            reject(new Error('Snowflake not configured'));
            return;
        }

        const connection = snowflake.createConnection(config);
        connection.connect((err, conn) => {
            if (err) {
                console.error('Unable to connect to Snowflake:', err);
                reject(err);
            } else {
                console.log('✅ Successfully connected to Snowflake');
                resolve(conn);
            }
        });
    });
}

// Execute Snowflake query
function executeQuery(connection, sqlText, binds = []) {
    return new Promise((resolve, reject) => {
        connection.execute({
            sqlText: sqlText,
            binds: binds,
            complete: (err, stmt, rows) => {
                if (err) {
                    console.error('Failed to execute statement:', err);
                    reject(err);
                } else {
                    resolve(rows);
                }
            }
        });
    });
}

// Initialize database tables
async function initializeDatabase() {
    const config = getSnowflakeConfig();
    if (!config) {
        console.log('📝 Running in LOCAL MODE - evidence will be stored in memory only');
        return false;
    }

    try {
        const connection = await createSnowflakeConnection();

        // Create database if not exists
        await executeQuery(connection, `CREATE DATABASE IF NOT EXISTS ${process.env.SNOWFLAKE_DATABASE}`);
        await executeQuery(connection, `USE DATABASE ${process.env.SNOWFLAKE_DATABASE}`);
        await executeQuery(connection, `USE SCHEMA ${process.env.SNOWFLAKE_SCHEMA}`);

        // Create forensic evidence table
        const createTableSQL = `
            CREATE TABLE IF NOT EXISTS FORENSIC_EVIDENCE (
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
        `;

        await executeQuery(connection, createTableSQL);
        console.log('✅ Database tables initialized successfully');

        connection.destroy();
        return true;
    } catch (error) {
        console.error('❌ Error initializing database:', error);
        console.log('📝 Falling back to LOCAL MODE');
        return false;
    }
}// API Routes

// Test endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Server is running' });
});

// Check if Snowflake is available
app.get('/api/snowflake/status', (req, res) => {
    const config = getSnowflakeConfig();
    res.json({
        configured: config !== null,
        account: config ? config.account : null
    });
});

// Test Snowflake connection
app.get('/api/snowflake/test', async (req, res) => {
    const config = getSnowflakeConfig();

    if (!config) {
        return res.json({
            success: false,
            message: 'Snowflake not configured',
            mode: 'local'
        });
    }

    try {
        console.log('Testing Snowflake connection...');
        const connection = await createSnowflakeConnection();

        // Run a simple test query
        const result = await executeQuery(connection, 'SELECT CURRENT_VERSION() as VERSION, CURRENT_ACCOUNT() as ACCOUNT, CURRENT_USER() as USER');

        connection.destroy();

        res.json({
            success: true,
            message: 'Successfully connected to Snowflake!',
            mode: 'snowflake',
            details: {
                version: result[0]?.VERSION,
                account: result[0]?.ACCOUNT,
                user: result[0]?.USER,
                database: config.database,
                warehouse: config.warehouse
            }
        });
    } catch (error) {
        console.error('Snowflake connection test failed:', error);
        res.json({
            success: false,
            message: 'Failed to connect to Snowflake',
            mode: 'local',
            error: error.message
        });
    }
});

// Upload forensic evidence
app.post('/api/evidence/forensic', upload.array('files'), async (req, res) => {
    const config = getSnowflakeConfig();

    // If Snowflake not configured, save locally only
    if (!config) {
        const files = req.files || [];
        return res.json({
            success: true,
            message: 'Evidence saved locally (Snowflake not configured)',
            fileCount: files.length,
            mode: 'local'
        });
    }

    try {
        const { caseNumber, description, collectedBy, dateCollected, timeCollected, location } = req.body;

        // Validate required fields
        if (!description || !collectedBy || !dateCollected || !location) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Get file information
        const files = req.files || [];
        const fileNames = files.map(f => f.originalname).join(', ');
        const fileCount = files.length;

        // Prepare metadata
        const metadata = {
            files: files.map(f => ({
                originalName: f.originalname,
                savedName: f.filename,
                size: f.size,
                mimetype: f.mimetype
            }))
        };

        // Connect to Snowflake and insert data
        const connection = await createSnowflakeConnection();

        const insertSQL = `
            INSERT INTO FORENSIC_EVIDENCE
            (CASE_NUMBER, DESCRIPTION, COLLECTED_BY, DATE_COLLECTED, TIME_COLLECTED, LOCATION, FILE_NAMES, FILE_COUNT, METADATA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, PARSE_JSON(?))
        `;

        await executeQuery(connection, insertSQL, [
            caseNumber || 'N/A',
            description,
            collectedBy,
            dateCollected,
            timeCollected,
            location,
            fileNames,
            fileCount,
            JSON.stringify(metadata)
        ]);

        connection.destroy();

        res.json({
            success: true,
            message: 'Forensic evidence uploaded to Snowflake successfully',
            fileCount: fileCount,
            mode: 'snowflake'
        });

    } catch (error) {
        console.error('Error uploading forensic evidence:', error);
        // Fallback to local storage if Snowflake fails
        const files = req.files || [];
        res.json({
            success: true,
            message: 'Evidence saved locally (Snowflake upload failed)',
            fileCount: files.length,
            mode: 'local',
            warning: error.message
        });
    }
});

// Get all forensic evidence
app.get('/api/evidence/forensic', async (req, res) => {
    try {
        const connection = await createSnowflakeConnection();

        const selectSQL = `
            SELECT EVIDENCE_ID, CASE_NUMBER, DESCRIPTION, COLLECTED_BY,
                   DATE_COLLECTED, TIME_COLLECTED, LOCATION, FILE_NAMES,
                   FILE_COUNT, SUBMITTED_AT
            FROM FORENSIC_EVIDENCE
            ORDER BY SUBMITTED_AT DESC
        `;

        const rows = await executeQuery(connection, selectSQL);
        connection.destroy();

        res.json({ success: true, data: rows });

    } catch (error) {
        console.error('Error fetching forensic evidence:', error);
        res.status(500).json({
            error: 'Failed to fetch evidence',
            details: error.message
        });
    }
});

// Start server
app.listen(PORT, async () => {
    console.log(`\n🚔 Detective Evidence System Server`);
    console.log(`📡 Server running on http://localhost:${PORT}`);
    console.log('━'.repeat(50));

    const snowflakeReady = await initializeDatabase();

    console.log('━'.repeat(50));
    if (snowflakeReady) {
        console.log('✅ SNOWFLAKE MODE: Evidence will be stored in Snowflake');
    } else {
        console.log('📝 LOCAL MODE: Evidence will be stored locally only');
        console.log('💡 To enable Snowflake, configure your .env file');
    }
    console.log('━'.repeat(50));
    console.log('Ready to accept evidence uploads!\n');
});
