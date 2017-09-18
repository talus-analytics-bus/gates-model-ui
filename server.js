var app = require('express')();
var server = require('http').Server(app);
var path = require('path');

var PythonShell = require('python-shell');


// Routing
app.get('/', function(req, res) {
	res.sendFile(path.join(__dirname, '/', 'index.html'));
});
app.get(/^(.+)$/, function(req, res) {
	if (req.params[0] === '/runModel') {
		console.log('running model!')
		// set up python shell and send inputs to script
		var pyshell = new PythonShell('py/gates-model.py', {mode: 'json'});
		pyshell.on('message', function(results) {
			res.send(results); // send outputs back
		});
		pyshell.send(req.query).end(function(err) {
			if (err) res.send({error: err});
		});
	} else {
		res.sendFile(path.join(__dirname, '/', req.params[0]));
	}
});	

// Start the HTTP Server
server.listen(process.env.PORT || 8888, function() {
	console.log('Server set up!');
	console.log(server.address());
});