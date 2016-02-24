var http = require('http');
http.createServer(function(request, response) {
	response.writeHead(200, {'Content-Type': 'text/plain'});
	response.write('Testing... this should work.');
	response.end();
}).listen(process.env.PORT || 8888);

var express = require('express');

/*var app = require('express')();
var server = require('http').Server(app);
var path = require('path');
var PythonShell = require('python-shell');

// HTTP Server feedback behavior
app.get('/', function(req, res) {
	res.sendFile(path.join(__dirname, '/', 'index.html'));
});
app.get(/^(.+)$/, function(req, res) {
	res.sendFile(path.join(__dirname, '/', req.params[0]));
});	

// Start the HTTP Server
server.listen(process.env.PORT || 8888, function() {
	console.log('Server set up!');
	console.log(server.address());
});

PythonShell.run('test.py', {
	mode: 'text',
	pythonOptions: ['-u'],
	scriptPath: 'py',
	args: ['testinput']
}, function(err, results) {
	if (err) throw err;
	console.log(results);
});*/
