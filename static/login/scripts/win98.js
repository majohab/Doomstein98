// Clock

let date = new Date();

setInterval(function () {
  document.querySelector('.time').innerText = date.toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });
}, 1000);

setTimeout(function () {
  document.querySelector('#boot').style.display = 'none';
}, 0);

setTimeout(function () {
  document.querySelector('#boot-ready').style.display = 'none';
}, 0);

// Dom manipulation

function clearWindow() {
    
}