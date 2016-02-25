var App = App || {};

(function() {
	App.initialize = function() {
		$('.header-title').click(function() { hasher.setHash(''); });
		
		// test python call
		var args = {input: 'testing 1,2'};
		$.get('/runModel', args, function(data) {
			console.log('got data');
			console.log(data);
		});
	};	
})();