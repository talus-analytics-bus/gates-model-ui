var App = App || {};

(function() {
	App.initialize = function() {
		$('.header-title').click(function() { hasher.setHash(''); });
	};
	
	App.initHome = function() {
		var popAgeData = [
			{age: '0-4', value: 0.05},
			{age: '5-10', value: 0.15},
			{age: '11-17', value: 0.20},
			{age: '18+', value: 0.60},
		];
		
		// population age section
		d3.selectAll('.pop-age-table input')
			.property('value', function(d, i) { return Util.percentize(popAgeData[i].value); })
			.on('change', function(d, i) {
				popAgeData[i].value = Util.formatInputVal(this);
				checkPopAgeSum();
				updatePopAgeChart();
			});
		
		var checkPopAgeSum = function() {
			var sum = 0;
			for (var i = 0; i < popAgeData.length; i++) sum += popAgeData[i].value;
			$('.pop-age-table tbody tr:last-child td:nth-child(2)').text(Util.percentize(sum));
			if (Math.abs(sum - 1) < 0.001) {
				$('.pop-age-warning').slideUp();
			} else {
				$('.pop-age-warning').slideDown();
			}
		};
		
		// build bar chart for the population age distribution
		var margin = {top: 45, right: 20, bottom: 25, left: 100};
		var width = 420 - margin.left - margin.right;
		var height = 220 - margin.top - margin.bottom;
   		var chart = d3.select('.pop-age-chart')
   			.attr('width', width + margin.left + margin.right)
   			.attr('height', height + margin.top + margin.bottom)
   			.append('g')
   				.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

		var x = d3.scale.ordinal()
			.domain(popAgeData.map(function(d) { return d.age; }))
			.rangeRoundBands([0, width], 0.2);
		var xAxis = d3.svg.axis().scale(x)
			.orient('bottom');
		var xAxisG = chart.append('g')
			.attr('class', 'x axis')
			.attr('transform', 'translate(0,' + height + ')')
			.call(xAxis);
			
		var y = d3.scale.linear()
			.domain([0, 1])
			.range([height, 0]);
		var yAxis = d3.svg.axis()
			.orient('left')
			.ticks(5)
			.tickFormat(Util.percentize)
			.innerTickSize(-width)
			.outerTickSize(0)
			.scale(y);
		var yAxisG = chart.append('g')
			.attr('class', 'y axis')
			.call(yAxis);
				
		var updatePopAgeChart = function() {
			var bars = chart.selectAll('rect')
				.data(popAgeData);
			var newBars = bars.enter().append('rect');
			bars
				.attr('x', function(d) { return x(d.age); })
				.attr('y', function(d) { return y(d.value); })
				.attr('width', x.rangeBand())
				.attr('height', function(d) { return height - y(d.value); });
			bars.exit().remove();
		};
		updatePopAgeChart();
		
		
		// multiselect for age range
		$('.schisto-age-select').multiselect();
		
		
		// malaria transmission pattern
		$('.malaria-timing-select').on('change', function() {
			if ($(this).val() === 'seasonal') $('.malaria-month-container').slideDown();
			else $('.malaria-month-container').slideUp();
		});
		$('.malaria-month-select').multiselect();
		
		
		// checkboxes for IRS and ITN
		$('.irs-checkbox').on('change', function() {
			$('.irs-true-contents').slideToggle();
			updateDistributionBlock();
		});
		$('.itn-checkbox').on('change', function() {
			$('.itn-true-contents').slideToggle();
			updateDistributionBlock();
		});
		var updateDistributionBlock = function() {
			var show = $('.irs-checkbox').is(':checked') && $('.itn-checkbox').is(':checked');
			if (show) $('.input-subsection[name="distribution-strategy"]').slideDown();
			else $('.input-subsection[name="distribution-strategy"]').slideUp();
		};
		
		
		// submit button
		$('.input-submit-button').click(function() { hasher.setHash('output'); });
	};
	
	App.initOutput = function() {
		var data = [
			{type: 'without integration', schisto: 0.36, malaria: 0.42},
			{type: 'with integration', schisto: 0.23, malaria: 0.30}
		];
		
		// fill table
		d3.selectAll('.output-table tbody tr').each(function(d, i) {
			d3.select(this).select('td:nth-child(2)').text(Util.percentize(data[i].schisto));
			d3.select(this).select('td:nth-child(3)').text(Util.percentize(data[i].malaria));
		});
		
		var barData = [
			{type: 'without integration', disease: 'schisto', value: 0.36},
			{type: 'without integration', disease: 'malaria', value: 0.42},
			{type: 'with integration', disease: 'schisto', value: 0.23},
			{type: 'with integration', disease: 'malaria', value: 0.30}
		];
		
		// build bar chart for the population age distribution
		var margin = {top: 30, right: 20, bottom: 80, left: 80};
		var width = 650 - margin.left - margin.right;
		var height = 250 - margin.top - margin.bottom;
   		var chart = d3.select('.output-bar-chart')
   			.attr('width', width + margin.left + margin.right)
   			.attr('height', height + margin.top + margin.bottom)
   			.append('g')
   				.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

		var x = d3.scale.ordinal()
			.domain(Util.getUnique(barData.map(function(d) { return d.disease; })))
			.rangeRoundBands([0, width], 0.5);
		var xAxis = d3.svg.axis().scale(x)
			.orient('bottom');
		var xAxisG = chart.append('g')
			.attr('class', 'x axis')
			.attr('transform', 'translate(0,' + height + ')')
			.call(xAxis);
			
		var y = d3.scale.linear()
			.domain([0, 0.5])
			.range([height, 0]);
		var yAxis = d3.svg.axis()
			.orient('left')
			.ticks(5)
			.tickFormat(Util.percentize)
			.innerTickSize(-width)
			.outerTickSize(0)
			.scale(y);
		var yAxisG = chart.append('g')
			.attr('class', 'y axis')
			.call(yAxis);
				
		// bars
		var bars = chart.selectAll('rect')
			.data(barData);
		var newBars = bars.enter().append('rect')
			.attr('class', 'bar');
			
		bars
			.style('fill', function(d) { return (d.type === 'without integration') ? 'url(#diagonal-stripe-1)' : 'steelblue'; })
			.attr('x', function(d) {
				var xVal = x(d.disease) - 20;
				if (d.type === 'with integration') xVal += 40;
				return xVal;
			})
			.attr('y', function(d) { return y(d.value); })
			.attr('width', x.rangeBand())
			.attr('height', function(d) { return height - y(d.value); });
		bars.exit().remove();
		
		// add legend
		var legend = chart.append('g')
			.attr('class', 'legend')
			.attr('transform', 'translate(100,' + (height+50) + ')');
		var legendGroups = legend.selectAll('g')
			.data(Util.getUnique(barData.map(function(d) { return d.type; })))
			.enter().append('g')
				.attr('transform', function(d, i) { return 'translate(' + (200*i) + ')'; });
		legendGroups.append('rect')
			.attr('width', 15)
			.attr('height', 15)
			.style('fill', function(d) { return (d === 'without integration') ? 'url(#diagonal-stripe-1)' : 'steelblue'; });
		legendGroups.append('text')
			.attr('transform', 'translate(25,13)')
			.text(function(d) { return d; });
	};
	
	App.initialize();
	Routing.precompileTemplates();	
	Routing.initializeRoutes();	
})();