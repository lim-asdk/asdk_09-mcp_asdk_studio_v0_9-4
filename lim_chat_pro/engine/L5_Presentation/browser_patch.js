/**
 * browser_patch.js
 * Enables MCP ASDK Studio to function in standard browsers (Chrome, etc.)
 * by redirecting pywebview calls to the internal HTTP server API.
 */

(function() {
    console.log("[ASDK] Initializing Browser Patch...");

    // Check if we are in a standard browser (no pywebview)
    if (!window.pywebview) {
        console.log("[ASDK] Non-pywebview environment detected. Activating Fetch Bridge.");

        window.pywebview = {
            api: new Proxy({}, {
                get: function(target, prop) {
                    return function(...args) {
                        console.log(`[ASDK] Browser API Call: ${prop}`, args);
                        
                        // Send request to the Python Hub's REST endpoint
                        return fetch('/api/call', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: json_robust_stringify({
                                method: prop,
                                args: args
                            })
                        })
                        .then(response => {
                            if (!response.ok) throw new Error('Network response was not ok');
                            return response.json();
                        })
                        .then(data => {
                            if (data.status === 'success') {
                                return data.result;
                            } else {
                                console.error("[ASDK] API Error:", data.message);
                                throw new Error(data.message);
                            }
                        });
                    };
                }
            })
        };
    }

    // Helper to handle circular references or complex objects if any
    function json_robust_stringify(obj) {
        try {
            return JSON.stringify(obj);
        } catch (e) {
            return JSON.stringify({ error: "Serialization failed" });
        }
    }
})();
