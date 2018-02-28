var App = App || {};

(function() {
	App.initOutput = function() {
		if ($.isEmptyObject(App.outputs)) {
			hasher.setHash('');
			return false;
		}
		
		// define variables
		var windowWidth = $(window).width();
		var isSeasonal = (App.inputs.malaria_timing === 'seasonal');


		// determine recommendation
		var isRecommended = (App.outputs.separate.malaria - App.outputs.integrated.malaria >= 0.05);
		var recOutput = isRecommended ? App.outputs.integrated : App.outputs.separate;

		// update recommendation text
		d3.select('.output-recommendation-text')
			.text(isRecommended ? 'INTEGRATED INTERVENTIONS' : 'NON-INTEGRATED INTERVENTIONS')
			.classed('text-success', isRecommended);
			
		// attach tooltip to question mark beside rec text
		var nonIntContentStr = '<b>Non-integrated interventions</b> represents the current strategy using the ' +
			'user-supplied schedule for schistosomiasis and malaria control measures';
		var intContentStr = '<b>Integrated interventions</b> entails distributing schistosomiasis and malaria ' +
			'control measures together and prior to any seasonal increase in malaria transmission.';
		var recContentStr = 'This is the <b>recommended</b> strategy for the user.';
		if (isRecommended) intContentStr += ' ' + recContentStr;
		else nonIntContentStr += ' ' + recContentStr;
		$('.output-recommendation .explanation-icon').tooltipster({
			maxWidth: 450,
			contentAsHTML: true,
			content: nonIntContentStr + '<br><br>' + intContentStr
		});
		
		// fill table showing prevalence
		d3.selectAll('.output-table tbody tr').each(function(d, i) {
			var outputs = (i === 0) ? App.outputs.separate : App.outputs.integrated;
			
			// populate cells with prevalence value
			var cells = d3.select(this).selectAll('td:nth-child(3), td:nth-child(4)').text(function(dd, j) {
				var val = (j === 0) ? outputs.schisto : outputs.malaria;
				return Util.percentize(val);
			});
			
			// apply green or red to "with integration" cells
			if (i === 1) {
				cells
					.classed('text-success', function(dd, j) {
						var disease = (j === 0) ? 'schisto' : 'malaria';
						return (Math.round(100*App.outputs.separate[disease]) - Math.round(100*App.outputs.integrated[disease]) >= 2);
					})
					.classed('text-danger', function(dd, j) {
						var disease = (j === 0) ? 'schisto' : 'malaria';
						return (Math.round(100*App.outputs.integrated[disease]) - Math.round(100*App.outputs.separate[disease]) >= 2);
					});
			}
		});
		
		// add arrow to recommended row for prevalence
		var recRowNum = isRecommended ? 2 : 1;
		d3.select('.output-table tbody tr:nth-child(' + recRowNum + ') td:first-child').append('img')
			.attr('class', 'arrow-icon')
			.attr('src', 'img/chevron_right.png');
		
		// build bar chart for the population age distribution
		var barData = [
			{type: 'without integration', disease: 'schisto', value: App.outputs.separate.schisto},
			{type: 'without integration', disease: 'malaria', value: App.outputs.separate.malaria},
			{type: 'with integration', disease: 'schisto', value: App.outputs.integrated.schisto},
			{type: 'with integration', disease: 'malaria', value: App.outputs.integrated.malaria}
		];
		
		var margin = {top: 10, right: 25, bottom: 80, left: 70};
		var chartWidth = (windowWidth < 670) ? windowWidth - 20 : 650;
		var width = chartWidth - margin.left - margin.right;
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
		
		// add axis label
		chart.append('text')
			.attr('class', 'axis-label')
			.attr('transform', 'rotate(-90)')
			.attr('x', -height/2)
			.attr('y', -55)
			.text('% Prevalence');
		
		// add legend
		var legendXCoord = (chartWidth < 450) ? 0 : (chartWidth-450)/2;
		var legend = chart.append('g')
			.attr('class', 'legend')
			.attr('transform', 'translate(' + legendXCoord + ',' + (height+50) + ')');
		var legendGroups = legend.selectAll('g')
			.data(Util.getUnique(barData.map(function(d) { return d.type; })))
			.enter().append('g')
				.attr('transform', function(d, i) { return 'translate(' + (225*i) + ')'; });
		legendGroups.append('rect')
			.attr('width', 15)
			.attr('height', 15)
			.style('fill', function(d) { return (d === 'without integration') ? 'url(#diagonal-stripe-1)' : 'steelblue'; });
		legendGroups.append('text')
			.attr('class','legend-label')
			.attr('transform', 'translate(25,13)')
			.text(function(d) { return d; });
		
		
		// add tooltips to question marks
		$('.output-table-container .explanation-icon:first-child').tooltipster({
			maxWidth: 400,
			contentAsHTML: true,
			content: 'The values shown are prevalence values for schistosomiasis and malaria when ' +
				'<b>non-integrated interventions</b> are used'
		});
		$('.output-table-container .explanation-icon:nth-child(2)').tooltipster({
			maxWidth: 450,
			contentAsHTML: true,
			content: 'The values shown are prevalence values for schistosomiasis and malaria when ' +
				'<b>integrated interventions</b> are used. ' +
				'<br><br>Values are colored <b>green</b> if there is a non-trival reduction in prevalence (> 1% reduction). ' + 
				'<br><br>Values are colored <b>red</b> if there is a non-trivial increase in prevalence (> 1% increase).'
		});
			
		
		/* ----------------------- Distribution Strategy Table ------------------------------- */
		var formatMonth = function(monthNum) {
			return d3.time.format('%B')(new Date(2015, monthNum-1, 1, 0, 0, 0, 0));
		};
		
		// update control measure recommended execution times
		d3.select('#rec_pzq_month').text(formatMonth(recOutput.pzq_month));
		
		if (App.inputs.irs) d3.select('#rec_spray_month').text(formatMonth(recOutput.spray_month));
		else $('.output-strategy-table tbody tr:nth-child(2)').hide();
		
		if (App.inputs.itn) d3.select('#rec_net_month').text(formatMonth(recOutput.net_month));
		else $('.output-strategy-table tbody tr:nth-child(3)').hide();


		/* ----------------------- Distribution Strategy Timeline ------------------------------- */
		var currMonthsEqualRec = (+App.inputs.schisto_month_num === +recOutput.pzq_month &&
			+App.inputs.irs_month_num === +recOutput.spray_month &&
			+App.inputs.itn_month_num === +recOutput.net_month);
		var timelineMargin = {top: 20, right: 105, bottom: (isSeasonal ? 105 : 70), left: 105};
		var timelineTotalWidth = (windowWidth < 820) ? windowWidth - 20 : 800;
		var timelineWidth = timelineTotalWidth - margin.left - margin.right;
		var timHeight = 60;
		var timSep = 20;
		var timelineHeight = currMonthsEqualRec ? timHeight : 2*timHeight + timSep;
		var timeline = d3.select('.output-timeline')
			.attr('width', timelineWidth + timelineMargin.left + timelineMargin.right)
			.attr('height', timelineHeight + timelineMargin.top + timelineMargin.bottom)
			.append('g')
				.attr('transform', 'translate(' + timelineMargin.left + ',' + timelineMargin.top + ')');
		
		var timelineCurr = timeline.append('g')
			.attr('class', 'timeline-group');
		var timelineRec = timeline.append('g')
			.attr('class', 'timeline-group')
			.attr('transform', 'translate(0,' + (timHeight+timSep) + ')');
		var timelineGroups = timeline.selectAll('.timeline-group');
		timelineCurr.append('rect')
			.attr('class', 'timeline-base')
			.attr('width', timelineWidth)
			.attr('height', timHeight);
		timelineRec.append('rect')
			.attr('class', 'timeline-base')
			.attr('width', timelineWidth)
			.attr('height', timHeight);

		// establish dates
		var getMonthXCoord = function(monthNum) { return timelineX(new Date(2015, monthNum-1, 1, 0, 0, 0, 0)); };
		var startTime = new Date(2015, 0, 1, 0, 0, 0, 0); // 3 months before seasonal starts
		var endTime = new Date(2016, 0, 1, 0, 0, 0, 0);
		
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

		// adjust axes labels
		$('.output-timeline .x.axis .tick text')
			.attr('x', timelineWidth/24)
			.attr('y', 8)
			.last()
				.css('display', 'none');
		
		// add seasonal bar
		if (isSeasonal) {
			timelineGroups.selectAll('.timeline-seasonal-base')
				.data(App.inputs.malaria_peak_month_num)
				.enter().append('rect')
					.attr('class', 'timeline-seasonal-base')
					.attr('x', function(d) { return getMonthXCoord(d); })
					.attr('width', function(d) { return getMonthXCoord(+d+1) - getMonthXCoord(d); })
					.attr('height', timHeight);
		}
			
		// add labels
		var currLabel = timelineCurr.append('text')
			.attr('class', 'y-label')
			.attr('x', -15)
			.attr('y', timHeight/2 + 3)
			.text('current');
		if (currMonthsEqualRec) {
			currLabel
				.attr('x', -33)
				.attr('y', timHeight/2 - 6);
			timelineCurr.append('text')
				.attr('class', 'y-label')
				.attr('x', -10)
				.attr('y', timHeight/2 + 10)
				.text('(recommended)');
		} else {
			timelineRec.append('text')
				.attr('class', 'y-label')
				.attr('x', -15)
				.attr('y', timHeight/2 + 3)
				.text('recommended');
		}
		
		// draw rectangles showing mitigation strategies
		var markerHeight = 10;
		var drawStrat = function(t, monthNum, text, yVal) {
			// calculate x-coordinates for the month supplied
			if (typeof monthNum === 'string') monthNum = +monthNum;
			var monthXCoord = getMonthXCoord(monthNum);
			var nextMonthXCoord = getMonthXCoord(monthNum+1);
			
			// draw the marker
			var stratGroup = t.append('g')
				.attr('class', 'strat-group')
				.attr('transform', 'translate(' + monthXCoord + ',' + yVal + ')');
			stratGroup.append('rect')
				.attr('class', 'strat-marker')
				.attr('y', -markerHeight/2)
				.attr('width', nextMonthXCoord - monthXCoord)
				.attr('height', markerHeight);
			var label = stratGroup.append('text')
				.attr('x', -7)
				.attr('y', 4)
				.text(text);
			if (monthXCoord === 0) {
				label
					.style('text-anchor', 'start')
					.attr('x', nextMonthXCoord + 7);
			}
			return monthXCoord;
		};
		
		var numTreats = App.inputs.itn + App.inputs.irs + 1;
		var treatCoords = (numTreats === 2) ? [20, 40] : [12, 30, 48];
		var currPzqX = drawStrat(timelineCurr, App.inputs.schisto_month_num, 'PZQ', treatCoords[0]);
		var recPzqX = drawStrat(timelineRec, recOutput.pzq_month, 'PZQ', treatCoords[0]);
		if (App.inputs.irs) {
			var currIrsX = drawStrat(timelineCurr, App.inputs.irs_month_num, 'IRS', treatCoords[1]);
			var recIrsX = drawStrat(timelineRec, recOutput.spray_month, 'IRS', treatCoords[1]);
		}
		if (App.inputs.itn) {
			var currItnX = drawStrat(timelineCurr, App.inputs.itn_month_num, 'ITN', (numTreats === 2) ? treatCoords[1] : treatCoords[2]);
			var recItnX = drawStrat(timelineRec, recOutput.net_month, 'ITN', (numTreats === 2) ? treatCoords[1] : treatCoords[2]);
		}
		
		// draw borders around timelines
		timelineGroups.append('line')
			.attr('class', 'strat-divider')
			.attr('x2', timelineWidth)
			.attr('y1', 0)
			.attr('y2', 0);
		timelineGroups.append('line')
			.attr('class', 'strat-divider')
			.attr('x2', timelineWidth)
			.attr('y1', timHeight)
			.attr('y2', timHeight);
			
		// add legend
		var timelineLegend = timeline.append('g')
			.attr('class', 'timeline-legend')
			.attr('transform', 'translate(0,' + (timelineHeight+50) + ')');
		if (isSeasonal) {
			var seasonalGroup = timelineLegend.append('g')
				.attr('transform', 'translate(222,0)');
			seasonalGroup.append('rect')
				.attr('class', 'timeline-seasonal-base')
				.attr('y', -1)
				.attr('width', 60)
				.attr('height', 16);
			seasonalGroup.append('text')
				.attr('class', 'legend-text')
				.attr('x', 75)
				.attr('y', 12)
				.text('Malaria Season');
		}
		var legendStratGroup = timelineLegend.append('g')
			.attr('transform', 'translate(222,' + (isSeasonal ? 30 : 0) + ')');
		legendStratGroup.append('rect')
			.attr('class', 'strat-marker')
			.attr('y', 2)
			.attr('width', 60)
			.attr('height', markerHeight);
		legendStratGroup.append('text')
			.attr('x', 75)
			.attr('y', 12)
			.text('Distribution of Treatment');


		// populate timeline recommendation text
		if (currMonthsEqualRec) {
			$('.output-timeline-rec-text').html('The <b>current</b> distribution times used for PZQ, IRS, and ITN are also the <b>recommended</b> distribution times.');
			timelineGroups.style('display', function(d, i) { if (i === 1) return 'none'; });
		} else {
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
			$('.output-timeline-rec-text').html(recText);
		}


		/* ----------------------- Assumptions & Back to Inputs ------------------------------- */
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
