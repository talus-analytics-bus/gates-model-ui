var App = App || {};

(function() {
	App.inputs = null; // stores inputs for the current browser session
	App.outputs = null; // stores all the outputs
	
	App.initialize = function() {
		// get cookies if its exists
		App.outputs = App.getCookie('outputs');
		
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
				if (data.hasOwnProperty('error')) callback(data.error, null);
				else callback(null, data);
			});
	};


	/* ---------------------------- Cookie Functions ------------------------------ */
	// stores a cookie with a given name, value, and expiration time, in days
	App.setCookie = function(cname, cvalue, exdays) {
		if (typeof cvalue === 'object') cvalue = JSON.stringify(cvalue);
		if (typeof exdays === 'undefined') var exdays = 7;
		var d = new Date();
		d.setTime(d.getTime() + (exdays*24*60*60*1000));
		var expires = 'expires=' + d.toUTCString();
		document.cookie = cname + '=' + cvalue + '; ' + expires;
	};
	
	// retrieves the cookie with a given name
	App.getCookie = function(cname) {
		var name = cname + '=';
		var ca = document.cookie.split(';');
		for (var i = 0; i < ca.length; i++) {
			var c = ca[i].trim();
			if (c.indexOf(name) === 0) {
				var cookieStr = c.substring(name.length, c.length);
				return JSON.parse(cookieStr);
			}
		}
		return null;
	};
})();