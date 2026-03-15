/**
 * ws-client.js — WebSocket connection to the FastAPI server.
 * Calls onState(state) whenever world_state.json changes.
 */

export function connectWS(onState) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${proto}://${location.host}/ws`;
  let ws, retryDelay = 1000;

  function connect() {
    ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('[ws-client] Connected');
      retryDelay = 1000;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'state' && msg.data) {
          onState(msg.data);
        }
      } catch (e) {
        console.warn('[ws-client] Parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log(`[ws-client] Disconnected — retrying in ${retryDelay}ms`);
      setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 15000);
    };

    ws.onerror = (e) => console.warn('[ws-client] Error:', e);
  }

  connect();
  return { send: (data) => ws?.readyState === WebSocket.OPEN && ws.send(JSON.stringify(data)) };
}
