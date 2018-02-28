var App = App || {};

(function() {
	App.inputs = null; // stores inputs for the current browser session
	App.outputs = null; // stores all the outputs

	// Debug mode notional outputs
	App.useNotionalOutputs = true;
	App.notionalOutputs = [
	  {
	    "spray_month": "08",
	    "malaria": 0.386,
	    "net_month": "08",
	    "pzq_month": "08",
	    "use_integration": true,
	    "schisto": 0.34
	  },
	  {
	    "spray_month": "01",
	    "malaria": 0.44,
	    "net_month": "11",
	    "pzq_month": "04",
	    "use_integration": false,
	    "schisto": 0.34
	  }
	];
	// App.notionalOutputs = [
	//   {
	//     "spray_month": "08",
	//     "malaria": 0.37790136986301465,
	//     "net_month": "08",
	//     "pzq_month": "08",
	//     "use_integration": true,
	//     "schisto": 0.34499999999999975
	//   },
	//   {
	//     "spray_month": "01",
	//     "malaria": 0.4329643835616432,
	//     "net_month": "11",
	//     "pzq_month": "04",
	//     "use_integration": false,
	//     "schisto": 0.3430000000000001
	//   }
	// ];
	
	App.initialize = function() {
		// get cookies if its exists
		App.inputs = App.getCookie('inputs');
		App.outputs = App.getCookie('outputs');
		
		// clicking header in navbar navigates user to home screen
		$('.header-title').click(function() { hasher.setHash(''); });
		
		// setting noty defaults
		$.noty.defaults.layout = 'center';
		$.noty.defaults.type = 'warning';
	};
	
	App.runModel = function(inputs, callback) {
		if (App.useNotionalOutputs) {
			if (inputs.use_integration) return callback(null, App.notionalOutputs[0]);
			else return callback(null, App.notionalOutputs[1]);
		} else {
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
		}
	};


	/* ---------------------------- Cookie Functions ------------------------------ */
	// stores a cookie with a given name, value, and expiration time, in days
	App.setCookie = function(cname, cvalue, exdays) {
		if (typeof cvalue === 'object') cvalue = JSON.stringify(cvalue);
		if (cvalue.length >= 4094) console.log('Cookie is too long! (over 4094 bytes)');
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