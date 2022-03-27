const lobbyName = JSON.parse(document.getElementById('json-lobbyname').textContent);

const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/game/'
    + lobbyName
    + '/'
);

document.getElementById("headline").textContent = lobbyName;

chatSocket.onmessage = function(e) {
    console.log('onmessage');
};

chatSocket.onclose = function(e) {
    console.log('The socket closed unexpectedly');
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const message = document.querySelector('#chat-message-input').value;

    chatSocket.send(JSON.stringify({
        'message': message,
        'username': userName,
        'room': lobbyName
    }));
};