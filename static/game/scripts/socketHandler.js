function socketHandler_init()
{
    const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);
    document.title = lobbyName;

    const chatSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/game/'
        + lobbyName
        + '/'
    );

    chatSocket.onmessage = function(e) {
        console.log('onmessage');
    };

    chatSocket.onclose = function(e) {
        console.log('The socket closed unexpectedly');
    };
}