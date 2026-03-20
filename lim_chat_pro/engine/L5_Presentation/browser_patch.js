/**
 * browser_patch.js
 * Enables MCP ASDK Studio to function in standard browsers (Chrome, etc.)
 * by redirecting pywebview calls to the internal Hub Registry.
 */

(function() {
    // Port must match the one in run_beta_server.py
    const HUB_PORT = 2026; 

    if (!window.pywebview) {
        console.log(`[ASDK] Browser Mode Detected. Routing via Port ${HUB_PORT}`);

        window.pywebview = {
            api: new Proxy({}, {
                get: function(target, prop) {
                    return function(...args) {
                        return fetch('/api/call', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ method: prop, args: args })
                        })
                        .then(res => res.json())
                        .then(data => {
                            if (data.status === 'success') return data.result;
                            throw new Error(data.message);
                        });
                    };
                }
            })
        };

        // Fire the ready event for browser mode
        window.dispatchEvent(new Event('pywebviewready'));
    }
})();
