document.addEventListener('DOMContentLoaded', (event) => {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var outputElement = document.getElementById('output');
    var statusElement = document.getElementById('status');

    socket.on('output', function(msg) {
        // Create a new text node with the message data
        var content = document.createTextNode(msg.data + '\n');
        // Create a new div element to contain the text node
        var newLine = document.createElement('div');
        newLine.appendChild(content);
        // Insert the new line at the top of the output element
        outputElement.insertBefore(newLine, outputElement.firstChild);
    });
    
    

    socket.on('status', function(msg) {
        statusElement.innerText = msg.data;
    });

    socket.on('simulation_complete', function(data) {
        window.open(data.url, '_blank');
    });

    document.getElementById('update-button').onclick = function() {
        var simcData = document.getElementById('simc-data').value;
        socket.emit('update_simc_file', {simc_data: simcData});
    };
});
