var App = App || {};

(function() {
	App.initialize = function() {

	};
	
	App.initHome = function() {
		$('.pop-age-table input').on('change', function() {
			Util.formatInputVal(this);
		});
	};
	
	App.initialize();
	Routing.precompileTemplates();	
	Routing.initializeRoutes();	
})();