DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NvsN V8 Mission Control</title>
    <style>
        body { background-color: #121212; color: #00ff00; font-family: monospace; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { border: 1px solid #333; padding: 10px; background: #1e1e1e; height: 300px; overflow-y: auto; }
        h2 { border-bottom: 1px solid #444; padding-bottom: 5px; margin-top: 0; }
        .log-entry { margin-bottom: 5px; border-bottom: 1px solid #222; }
        .success { color: #00ff00; }
        .error { color: #ff0000; }
        .warning { color: #ffff00; }
        #network { height: 100%; width: 100%; }
    </style>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
    <h1>NvsN V8: OMEGA MISSION CONTROL</h1>
    <div class="grid">
        <div class="panel">
            <h2>Swarm Topology (Fractal Tree)</h2>
            <div id="network"></div>
        </div>
        <div class="panel">
            <h2>System Health (Global Tensor)</h2>
            <canvas id="healthChart"></canvas>
        </div>
    </div>
    <div class="grid" style="margin-top: 20px;">
        <div class="panel" style="grid-column: span 2;">
            <h2>Live Neural Feed</h2>
            <div id="logs"></div>
        </div>
    </div>

    <script>
        const ws = new WebSocket("ws://" + window.location.host + "/ws");
        const logsDiv = document.getElementById("logs");

        // Vis.js Network Setup
        const nodes = new vis.DataSet([]);
        const edges = new vis.DataSet([]);
        const container = document.getElementById('network');
        const data = { nodes: nodes, edges: edges };
        const options = {
            nodes: { shape: 'dot', size: 10, color: '#00ff00' },
            edges: { color: '#444' }
        };
        const network = new vis.Network(container, data, options);

        ws.onmessage = function(event) {
            const msg = JSON.parse(event.data);

            if (msg.type === "LOG") {
                const entry = document.createElement("div");
                entry.className = "log-entry " + (msg.level || "info");
                entry.innerText = `[${new Date().toLocaleTimeString()}] ${msg.content}`;
                logsDiv.prepend(entry);
                if (logsDiv.childElementCount > 50) logsDiv.lastChild.remove();
            } else if (msg.type === "TOPOLOGY") {
                // Update Graph
                if (msg.action === "add_node") {
                    try { nodes.add({id: msg.id, label: msg.label}); } catch(e){}
                } else if (msg.action === "add_edge") {
                    try { edges.add({from: msg.from, to: msg.to}); } catch(e){}
                }
            }
        };
    </script>
</body>
</html>
"""
