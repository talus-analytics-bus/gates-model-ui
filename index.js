var app = require('express')();
var server = require('http').Server(app);
var path = require('path');
var port = 3000;

var PythonShell = require('python-shell');


// HTTP Server feedback behavior
app.get('/', function(req, res) {
	res.sendFile(path.join(__dirname, '/', 'index.html'));
});
app.get(/^(.+)$/, function(req, res) {
	res.sendFile(path.join(__dirname, '/', req.params[0]));
});	

// Start the HTTP Server
server.listen(port, function() {
	console.log('Server set up! Listening to: localhost:' + port);
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
});
