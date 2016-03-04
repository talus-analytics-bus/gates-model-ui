var App = App || {};

(function() {
	App.outputs = {}; // stores all the outputs for a run
	
	App.initialize = function() {
		$('.header-title').click(function() { hasher.setHash(''); });	
	};
	
	App.runModel = function(inputs, callback) {
		NProgress.start();
		
		var now = new Date();
		console.log('starting model run...');

		$.get('/runModel', inputs)
			.always(function() {
				console.log('finished model run: ' + ((new Date() - now)/1000) + ' seconds');
				NProgress.done();
			})
			.fail(function() {
				console.log('error!');
				callback('error', null);
			})
			.done(function(data) {
				console.log('success!');
				console.log(data);
				if (data.hasOwnProperty('error')) callback(data.error, null);
				else callback(null, data);
			});
	};
})();