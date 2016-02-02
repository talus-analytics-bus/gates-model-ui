var App = App || {};

(function() {
	App.initialize = function() {

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
				adjustPopAgeSum(i);
				updatePopAgeChart();
			});
		
		var adjustPopAgeSum = function(indexChanged) {
			var sum = 0;
			for (var i = 0; i < popAgeData.length; i++) sum += popAgeData[i].value;
			var diff = sum - 1;
			for (var j = 0; j < popAgeData.length; j++) {
				if (j !== indexChanged) {
					if (popAgeData[j].value >= diff) {
						popAgeData[j].value -= diff;
						$('.pop-age-table input').eq(j).val(Util.percentize(popAgeData[j].value));
						break;
					} else {
						diff -= popAgeData[j].value;
						popAgeData[j].value = 0;
						$('.pop-age-table input').eq(j).val(Util.percentize(0));
					}
				}
			}
		};
		
		// build bar chart for the population age distribution
		var margin = {top: 30, right: 20, bottom: 30, left: 80};
		var width = 450 - margin.left - margin.right;
		var height = 200 - margin.top - margin.bottom;
   		var chart = d3.select('.pop-age-chart')
   			.attr('width', width + margin.left + margin.right)
   			.attr('height', height + margin.top + margin.bottom)
   			.append('g')
   				.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

		var x = d3.scale.ordinal()
			.domain(popAgeData.map(function(d) { return d.age; }))
			.rangeRoundBands([0, width], 0.3);
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
			
		var line = d3.svg.line()
			.x(function(d) { return x(d.age); })
			.y(function(d) { return y(d.value); })
			.interpolate('basis');
		var lineElement = chart.append('path')
			.attr('class', 'line')
			.attr('transform', 'translate(' + x.rangeBand()/2 + ',0)');
		
		
		var updatePopAgeChart = function() {
			lineElement
				.datum(popAgeData)
				.attr('d', line);
				
			// bars
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
		var margin = {top: 30, right: 20, bottom: 30, left: 80};
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
		var newBars = bars.enter().append('rect');
			
		bars
			.style('fill', function(d) { return (d.type === 'with integration') ? '#31a354' : 'steelblue'; })
			.attr('x', function(d) {
				var xVal = x(d.disease) - 20;
				if (d.type === 'with integration') xVal += 40;
				return xVal;
			})
			.attr('y', function(d) { return y(d.value); })
			.attr('width', x.rangeBand())
			.attr('height', function(d) { return height - y(d.value); });
		bars.exit().remove();
	};
	
	App.initialize();
	Routing.precompileTemplates();	
	Routing.initializeRoutes();	
})();