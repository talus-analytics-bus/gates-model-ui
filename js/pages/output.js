var App = App || {};

(function() {
	App.initOutput = function() {
		console.log(App.outputs);
		if ($.isEmptyObject(App.outputs)) {
			hasher.setHash('');
			return false;
		}
		
		// prevalence percentages for each disease for integrated and non-integrated
		var schistoPrevInt = App.outputs.integrated.schisto;
		var malariaPrevInt = App.outputs.integrated.malaria;
		var schistoPrevNoInt = App.outputs.separate.schisto;
		var malariaPrevNoInt = App.outputs.separate.malaria;
		
		
		// update recommendation text
		var isRecommended = malariaPrevInt < malariaPrevNoInt;
		d3.select('.output-recommendation')
			.text(isRecommended ? 'INTEGRATED TREATMENT' : 'NON-INTEGRATED TREATMENT')
			.classed('text-success', isRecommended);
		
		// fill table showing prevalence
		var data = [
			{type: 'without integration', schisto: schistoPrevNoInt, malaria: malariaPrevNoInt},
			{type: 'with integration', schisto: schistoPrevInt, malaria: malariaPrevInt}
		];
		d3.selectAll('.output-table tbody tr').each(function(d, i) {
			d3.select(this).select('td:nth-child(2)')
				.text(Util.percentize(data[i].schisto));
			d3.select(this).select('td:nth-child(3)')
				.text(Util.percentize(data[i].malaria))
				.classed('text-success', function() { if (i === 1) return (malariaPrevInt < malariaPrevNoInt); })
				.classed('text-danger', function() { if (i === 1) return (malariaPrevInt > malariaPrevNoInt); });
		});
		
		var barData = [
			{type: 'without integration', disease: 'schisto', value: schistoPrevNoInt},
			{type: 'without integration', disease: 'malaria', value: malariaPrevNoInt},
			{type: 'with integration', disease: 'schisto', value: schistoPrevInt},
			{type: 'with integration', disease: 'malaria', value: malariaPrevInt}
		];
		
		// build bar chart for the population age distribution
		var margin = {top: 30, right: 20, bottom: 80, left: 80};
		var width = 650 - margin.left - margin.right;
		var height = 300 - margin.top - margin.bottom;
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
			
		
		// update control measure recommended execution times
		var recOutput = isRecommended ? App.outputs.integrated : App.outputs.separate;		
		d3.select('#rec_pzq_month').text(recOutput.pzq_month);
		d3.select('#rec_net_month').text(recOutput.net_month);
		d3.select('#rec_spray_month').text(recOutput.spray_month);
		
		// toggling display of assumptions
		$('.assumption-bar').on('click', function() {
			var $bar = $(this);
			var $contents = $('.assumption-contents');
			var isHiding = $contents.is(':visible');
			$contents.slideToggle();
			$bar.find('.down-arrow').toggleClass('rotated');
			$bar.find('span').text(isHiding ? 'show assumptions' : 'hide assumptions');
		});
		
		
		// back to inputs button
		$('.input-back-button').click(function() { hasher.setHash(''); });
	};
})();
