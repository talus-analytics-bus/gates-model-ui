var App = App || {};

(function() {
	App.initialize = function() {
		$('.header-title').click(function() { hasher.setHash(''); });	
		
		// test the model out
		App.runModel({pop1: 0.2, pop2: 0.3, pop3: 0.4});
	
	};
	
	App.runModel = function(inputs) {
		NProgress.start();
		
		var now = new Date();
		console.log('starting model run...');

		$.get('/runModel', inputs, function(data) {
			console.log('finished model run: ' + ((new Date() - now)/1000) + ' seconds');
			console.log(data);
			NProgress.done();
		});
	};
})();