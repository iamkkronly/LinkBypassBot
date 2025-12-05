const express = require('express');
const bodyParser = require('body-parser');
const { execFile } = require('child_process');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use(express.static('public'));

app.post('/api/bypass', (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ error: 'No URL provided' });
    }

    // Call the Python script
    execFile('python3', ['cli.py', url], (error, stdout, stderr) => {
        if (error) {
            console.error('Error executing Python script:', error);
            // Fallback for Vercel: If this runs on Vercel Node runtime, it might fail to spawn python if not configured.
            // But on Vercel, requests to /api/bypass should be routed to api/index.py via vercel.json.
            // This code block is primarily for local execution or non-serverless Node hosting.
            return res.status(500).json({ error: 'Internal Server Error' });
        }

        try {
            const result = JSON.parse(stdout);
            res.json(result);
        } catch (parseError) {
            console.error('Error parsing JSON:', parseError);
            console.error('Stdout was:', stdout);
            res.status(500).json({ error: 'Failed to parse result' });
        }
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
