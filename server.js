var app = require('express')();
var server = require('http').Server(app);
var path = require('path');

var PythonShell = require('python-shell');


// set up python shell
var pyshell = new PythonShell('py/test.py', {mode: 'text'});
pyshell.on('message', function(results) {
	console.log(results);
});


// HTTP Server feedback behavior
app.get('/', function(req, res) {
	res.sendFile(path.join(__dirname, '/', 'index.html'));
});
app.get(/^(.+)$/, function(req, res) {
	if (req.params[0] === '/runModel') {
		//console.log(req.query);
		
		PythonShell.run('test.py', {
			mode: 'text',
			pythonOptions: ['-u'],
			scriptPath: 'py',
			args: ['test2']
		}, function(err, results) {
			if (err) throw err;
			res.send(results);
		});
		
		//pyshell.send('hello');
		/*pyshell.on('message', function(results) {
			console.log(results);
		});*/
		
	} else {
		res.sendFile(path.join(__dirname, '/', req.params[0]));
	}
});	

// Start the HTTP Server
server.listen(process.env.PORT || 8888, function() {
	console.log('Server set up!');
	console.log(server.address());
});