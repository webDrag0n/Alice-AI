const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const { BotManager } = require('./bot');

const app = express();
const port = 3000;

app.use(bodyParser.json());

// Load config
let config = {};
try {
    const configPath = path.join(__dirname, '../config.json');
    if (fs.existsSync(configPath)) {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        console.log('Loaded config from config.json');
    } else {
        console.log('No config.json found, using defaults/request body');
    }
} catch (e) {
    console.warn("Could not load config.json", e);
}

const botManager = new BotManager();

// Middleware to check if bot is ready
const checkBot = (req, res, next) => {
    if (!botManager.bot) {
        return res.status(503).json({ error: 'Bot not initialized' });
    }
    next();
};

// --- Management Endpoints ---

app.post('/start', (req, res) => {
    const { host, port, username, version, password, auth } = req.body;
    
    const botOptions = {
        host: host || config.host || 'localhost',
        port: port || config.port || 25565,
        username: username || config.username || 'AliceBot',
        version: version || config.version || false,
        password: password || config.password,
        auth: auth || config.auth || 'offline'
    };

    try {
        botManager.start(botOptions);
        res.json({ status: 'starting', message: 'Bot connection initiated' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/stop', (req, res) => {
    botManager.stop();
    res.json({ status: 'stopped' });
});

app.get('/status', (req, res) => {
    res.json(botManager.getStatus());
});

// --- Perception Endpoints ---

app.get('/perception', checkBot, (req, res) => {
    res.json(botManager.getPerception());
});

app.get('/inventory', checkBot, (req, res) => {
    res.json(botManager.getInventory());
});

app.get('/surroundings', checkBot, (req, res) => {
    res.json(botManager.getSurroundings());
});

// --- Action Endpoints ---

app.post('/action/chat', checkBot, (req, res) => {
    const { message } = req.body;
    botManager.chat(message);
    res.json({ status: 'sent' });
});

app.post('/action/move', checkBot, async (req, res) => {
    const { x, y, z } = req.body;
    try {
        await botManager.moveTo(x, y, z);
        res.json({ status: 'arrived' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/action/mine', checkBot, async (req, res) => {
    const { x, y, z } = req.body;
    try {
        await botManager.mineBlock(x, y, z);
        res.json({ status: 'mined' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/action/place', checkBot, async (req, res) => {
    const { x, y, z, face, itemName } = req.body; // face is vector
    try {
        await botManager.placeBlock(x, y, z, face, itemName);
        res.json({ status: 'placed' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/action/equip', checkBot, async (req, res) => {
    const { itemName, destination } = req.body;
    try {
        await botManager.equipItem(itemName, destination);
        res.json({ status: 'equipped' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/action/craft', checkBot, async (req, res) => {
    const { itemName, count } = req.body;
    try {
        await botManager.craftItem(itemName, count);
        res.json({ status: 'crafted' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/action/attack', checkBot, async (req, res) => {
    const { entityName } = req.body;
    try {
        await botManager.attackEntity(entityName);
        res.json({ status: 'attacked' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Minecraft Agent Interface listening at http://localhost:${port}`);
    
    // Auto-connect on startup if config is present
    if (config.host) {
        console.log("Initiating auto-connect with config...");
        try {
            botManager.start(config);
        } catch (e) {
            console.error("Auto-connect failed:", e);
        }
    }
});
