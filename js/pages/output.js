var App = App || {};

(function() {
	App.initOutput = function() {
		var schisto_prev = App.outputs.integrated.schisto;
		var malaria_prev = App.outputs.integrated.malaria;
		
		var data = [
			{type: 'without integration', schisto: App.outputs.separate.schisto, malaria: App.outputs.separate.malaria},
			{type: 'with integration', schisto: schisto_prev, malaria: malaria_prev}
		];
		
		// fill table
		d3.selectAll('.output-table tbody tr').each(function(d, i) {
			d3.select(this).select('td:nth-child(2)')
				.text(Util.percentize(data[i].schisto));
			d3.select(this).select('td:nth-child(3)').text(Util.percentize(data[i].malaria));
		});
		
		var barData = [
			{type: 'without integration', disease: 'schisto', value: 0.36},
			{type: 'without integration', disease: 'malaria', value: 0.42},
			{type: 'with integration', disease: 'schisto', value: schisto_prev},
			{type: 'with integration', disease: 'malaria', value: malaria_prev}
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
			.domain([0, 1.1*d3.max([data[0].schisto, data[0].malaria, data[1].schisto, data[1].malaria])])
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
			
			
		/* ----------------- Matrix --------------- */
		var matrixDiffData = [
			{type: '0.3', '30': [0.04, 0.04], '50': [0.03, 0.01], '80': [-0.03, 0.01], '100': [-0.13, 0.01]},
			{type: '0.5', '30': [0.02, -0.01], '50': [0.02, -0.01], '80': [-0.12, -0.03], '100': [-0.13, -0.01]},
			{type: '0.8', '30': [-0.01, -0.01], '50': [0.00, -0.06], '80': [-0.10, -0.07], '100': [-0.14, -0.08]},
			{type: '1', '30': [-0.01, -0.07], '50': [-0.05, -0.09], '80': [-0.09, -0.09], '100': [-0.14, -0.10]}
		];
		
		var colors = ['rgba(252,141,89,0.5)','rgba(254,224,139,0.5)','rgba(255,255,191,0.5)','rgba(217,239,139,0.65)','rgba(145,207,96,0.5)'];
		var diffColorScale = d3.scale.threshold()
			.domain([-0.095, -0.045, -0.025, 0.001])
			.range(colors);
		
		var updateMatrix = function(data) {
			var rows = d3.select('.output-matrix-table tbody').selectAll('tr')
				.data(data);
			var newRows = rows.enter().append('tr');
			
			var cells = rows.selectAll('td')
				.data(function(d) { return ['type', '30', '50', '80', '100'].map(function(dd) { return d[dd]; }); });
			cells.enter().append('td');
			
			rows.selectAll('td')
				.classed('success', function(d, i) { if (i > 0) return (d[0] + d[1]) / 2 < 0; })
				.classed('danger', function(d, i) { if (i > 0) return (d[0] + d[1]) / 2 > 0; })
				.html(function(d, i) {
					if (i === 0) return Util.percentize(d);
					else {
						var yesOrNo = ((d[0] + d[1]) / 2 < 0) ? 'YES' : 'NO';
						var numOneClass = (d[0] > 0) ? 'text-danger' : (d[0] < 0) ? 'text-success' : '';
						var numTwoClass = (d[1] > 0) ? 'text-danger' : (d[1] < 0) ? 'text-success' : '';
						
						var htmlStr = '<div class="matrix-cell-yes">' + yesOrNo + '</div>';
						htmlStr += '<div class="matrix-cell-perc">(';
						htmlStr += '<span class="' + numOneClass + '">' + Util.percentizeDiff(d[0]) + '</span>';
						htmlStr += ' / ';
						htmlStr += '<span class="' + numTwoClass + '">' + Util.percentizeDiff(d[1]) + '</span>';
						htmlStr += ')</div>';
						return htmlStr;
					}
				});	

			// add black border around relevant cell
			d3.select('.output-matrix-table tbody tr:nth-child(3) td:nth-child(4)')
				.style('font-weight', '600')
				.append('div').attr('class', 'selected-border-box');
		};
		updateMatrix(matrixDiffData);
		
		
		
		// back to inputs button
		$('.input-back-button').click(function() { hasher.setHash(''); });
	};
})();
