var App = App || {};

(function() {
	var init = function() {
		App.initialize();
		Routing.precompileTemplates();	
		Routing.initializeRoutes();
	};	
	init();
})();