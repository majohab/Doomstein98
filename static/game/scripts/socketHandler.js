function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    document.title = lobbyName;

    const webSocket = new WebSocket(
        'ws://'
        + '//localhost:8001' // window.location.host
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