function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    document.title = lobbyName;

    const protocol = window.location.protocol.match(/^https/) ? 'wss' : 'ws'

    const webSocket = new WebSocket(
        protocol
        + '://'
        + window.location.host
        + '/ws/game/'
        + lobbyName
        + '/'
    );

    webSocket.onmessage = function(e) {
        console.log('onmessage');
    };

    webSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly');
    };
}