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
		
		// determine recommendation
		var isSeasonal = (App.inputs.malaria_timing === 'seasonal');
		var isRecommended = malariaPrevInt < malariaPrevNoInt;
		var recOutput = isRecommended ? App.outputs.integrated : App.outputs.separate;


		// update recommendation text
		d3.select('.output-recommendation')
			.text(isRecommended ? 'INTEGRATED INTERVENTIONS' : 'NON-INTEGRATED INTERVENTIONS')
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
		var margin = {top: 20, right: 20, bottom: 80, left: 80};
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
			
		
		/* ----------------------- Distribution Strategy Timeline ------------------------------- */
		var timelineMargin = {top: 30, right: 20, bottom: (isSeasonal ? 100 : 65), left: 105};
		var timelineWidth = 800 - margin.left - margin.right;
		var timelineHeight = 120;
		var timeline = d3.select('.output-timeline')
			.attr('width', timelineWidth + timelineMargin.left + timelineMargin.right)
			.attr('height', timelineHeight + timelineMargin.top + timelineMargin.bottom)
			.append('g')
				.attr('transform', 'translate(' + timelineMargin.left + ',' + timelineMargin.top + ')');
				
		timeline.append('rect')
			.attr('class', 'timeline-base-current')
			.attr('width', timelineWidth)
			.attr('height', timelineHeight/2);
		timeline.append('rect')
			.attr('class', 'timeline-base-rec')
			.attr('y', timelineHeight/2)
			.attr('width', timelineWidth)
			.attr('height', timelineHeight/2);

		// establish dates
		var getMonthXCoord = function(monthNum, year) {
			if (typeof year === 'undefined') var year = 2015;
			return timelineX(new Date(year, monthNum-1, 1, 0, 0, 0, 0));
		};
		var malariaStartMonthNum = +App.inputs.malaria_peak_month_num[0];
		var malariaEndMonthNum = +App.inputs.malaria_peak_month_num[App.inputs.malaria_peak_month_num.length - 1];
		var startTime = new Date(2015, malariaStartMonthNum-4, 1, 0, 0, 0, 0); // 3 months before seasonal starts
		var endTime = new Date(2016, malariaStartMonthNum-4, 1, 0, 0, 0, 0);
		
		// establish timeline axis
		var timelineX = d3.time.scale()
			.domain([startTime, endTime])
			.range([0, timelineWidth]);
		var timelineXAxis = d3.svg.axis().scale(timelineX)
			.tickFormat(d3.time.format('%b'))
			.orient('bottom');
		timeline.append('g')
			.attr('class', 'x axis')
			.attr('transform', 'translate(0,' + timelineHeight + ')')
			.call(timelineXAxis);
		
		// add seasonal bar
		if (isSeasonal) {
			var malariaStartDate = getMonthXCoord(malariaStartMonthNum);
			var malariaEndDate = getMonthXCoord(malariaEndMonthNum);
			if (malariaEndDate < malariaStartDate) malariaEndDate = getMonthXCoord(malariaEndMonthNum, 2016);
			timeline.append('rect')
				.attr('class', 'timeline-seasonal-base')
				.attr('x', malariaStartDate)
				.attr('width', malariaEndDate - malariaStartDate)
				.attr('height', timelineHeight);
		}
			
		// add labels
		timeline.append('text')
			.attr('class', 'y-label')
			.attr('x', -10)
			.attr('y', timelineHeight/4 + 3)
			.text('current');
		timeline.append('text')
			.attr('class', 'y-label')
			.attr('x', -10)
			.attr('y', 3*timelineHeight/4 + 3)
			.text('recommended');
		
		// draw lines showing mitigation strategies
		var circleRadius = 5;
		var drawStrat = function(monthNum, className, text, yVal) {
			var monthXCoord = getMonthXCoord(monthNum);
			if (monthXCoord < 0) monthXCoord = getMonthXCoord(monthNum, 2016);
			var stratGroup = timeline.append('g')
				.attr('class', 'strat-group')
				.attr('transform', 'translate(' + monthXCoord + ',' + yVal + ')');
			stratGroup.append('circle')
				.attr('class', className)
				.attr('r', circleRadius);
			var label = stratGroup.append('text')
				.attr('x', -10)
				.attr('y', 4)
				.text(text);
			if (monthXCoord === 0) {
				label
					.style('text-anchor', 'start')
					.attr('x', 10);
			}
			return monthXCoord;
		};
		var currPzqX = drawStrat(App.inputs.schisto_month_num, 'current-strat-marker', 'PZQ', 12);
		var currIrsX = drawStrat(App.inputs.irs_month_num, 'current-strat-marker', 'IRS', 30);
		var currItnX = drawStrat(App.inputs.itn_month_num, 'current-strat-marker', 'ITN', 48);
		var recPzqX = drawStrat(recOutput.pzq_month, 'rec-strat-marker', 'PZQ', 72);
		var recIrsX = drawStrat(recOutput.spray_month, 'rec-strat-marker', 'IRS', 90);
		var recItnX = drawStrat(recOutput.net_month, 'rec-strat-marker', 'ITN', 108);
		
		// draw line separating strategies
		timeline.append('line')
			.attr('class', 'strat-divider')
			.attr('x2', timelineWidth)
			.attr('y1', timelineHeight/2)
			.attr('y2', timelineHeight/2);
			
		// add legend
		var timelineLegend = timeline.append('g')
			.attr('class', 'timeline-legend')
			.attr('transform', 'translate(0,' + (timelineHeight+45) + ')');
		if (isSeasonal) {
			var seasonalGroup = timelineLegend.append('g')
				.attr('transform', 'translate(222,0)');
			seasonalGroup.append('rect')
				.attr('class', 'timeline-seasonal-base')
				.attr('width', 60)
				.attr('height', 14);
			seasonalGroup.append('text')
				.attr('class', 'legend-text')
				.attr('x', 75)
				.attr('y', 12)
				.text('Malaria Season');
		}
		var legendStratGroup = timelineLegend.append('g')
			.attr('transform', 'translate(220,' + (isSeasonal ? 30 : 0) + ')');
		legendStratGroup.append('circle')
			.attr('class', 'current-strat-marker')
			.attr('r', circleRadius)
			.attr('cy', 7);
		legendStratGroup.append('text')
			.attr('x', circleRadius+10)
			.attr('y', 12)
			.text('Distribution of Treatment');


		// populate timeline recommendation text
		var recText = '';
		var treats = [];
		if (recPzqX < currPzqX) treats.push('<b>PZQ</b>');
		if (recIrsX < currIrsX) treats.push('<b>IRS</b>');
		if (recItnX < currItnX) treats.push('<b>ITN</b>');
		if (treats.length > 0) {
			var ttext = (treats.length === 1) ? 'treatment' : 'treatments';
			var verb = (treats.length === 1) ? 'is' : 'are';
			recText += 'It is recommended that the ' + ttext + ', ' + treats.join(', ') + ', ' + verb + ' applied at an earlier time.';
		}

		treats = [];
		if (recPzqX > currPzqX) treats.push('<b>PZQ</b>');
		if (recIrsX > currIrsX) treats.push('<b>IRS</b>');
		if (recItnX > currItnX) treats.push('<b>ITN</b>');
		if (treats.length > 0) {
			if (recText.length > 0) recText += '<br>';
			var etext = (treats.length === 1) ? 'treatment' : 'treatments';
			var verb = (treats.length === 1) ? 'is' : 'are';
			recText += 'It is recommended that the ' + etext + ', ' + treats.join(', ') + ', ' + verb + ' applied at a later time.';
		}
		if (recPzqX !== currPzqX || recIrsX !== currIrsX || recItnX !== currItnX) {
			$('.output-timeline-rec-text').html(recText);
		}



		/* ----------------------- Distribution Strategy Table ------------------------------- */
		var formatMonth = function(monthNum) {
			return d3.time.format('%B')(new Date(2015, monthNum-1, 1, 0, 0, 0, 0));
		};
		
		// update control measure recommended execution times
		d3.select('#rec_pzq_month').text(formatMonth(recOutput.pzq_month));
		d3.select('#rec_net_month').text(formatMonth(recOutput.net_month));
		d3.select('#rec_spray_month').text(formatMonth(recOutput.spray_month));
		
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
