var App = App || {};

(function() {
	App.outputs = {}; // stores all the outputs for a run
	
	App.initialize = function() {
		// clicking header in navbar navigates user to home screen
		$('.header-title').click(function() { hasher.setHash(''); });
		
		// setting noty defaults
		$.noty.defaults.layout = 'center';
		$.noty.defaults.type = 'warning';
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
				callback('error', null);
			})
			.done(function(data) {
				console.log(data);
				if (data.hasOwnProperty('error')) callback(data.error, null);
				else callback(null, data);
			});
	};
})();