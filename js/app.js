var App = App || {};

(function() {
	App.initialize = function() {
		$('.header-title').click(function() { hasher.setHash(''); });
	};
	
	App.initHome = function() {
		// opening and closing input sections
		$('.input-section .title').click(function() {
			var contents = $(this).next().find('.input-subsection, .next-button-container');
			var isShowing = contents.is(':visible');
			if (isShowing) {
				contents.slideUp();
			} else {
				$(this).parent().siblings('.input-section').find('.input-subsection, .next-button-container').slideUp();
				contents.slideDown();
			}
		});
		$('.next-button-container .btn').click(function() {
			var contents = $(this).parent().parent();
			contents.slideUp();
			contents.parent().next('.input-section').find('.input-subsection, .next-button-container').slideDown();
		});
		
		
		var popAgeData = [
			{age: '0-5', value: 0.20},
			{age: '5-15', value: 0.34},
			{age: '16+', value: 0.46},
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
		var margin = {top: 25, right: 20, bottom: 20, left: 100};
		var width = 420 - margin.left - margin.right;
		var height = 200 - margin.top - margin.bottom;
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
		
		
		// slide open first input section
		$('.input-section[name="pop-age"]').find('.input-subsection, .next-button-container').slideDown();
	};
	
	App.initOutput = function() {
		var data = [
			{type: 'without integration', schisto: 0.36, malaria: 0.42},
			{type: 'with integration', schisto: 0.23, malaria: 0.35}
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
			{type: 'with integration', disease: 'malaria', value: 0.35}
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
			
			
		/* ----------------- Matrix --------------- */
		var matrixWithoutData = [
			{type: '0.3', '30': 0.50, '50': 0.48, '80': 0.45, '100': 0.39},
			{type: '0.5', '30': 0.48, '50': 0.45, '80': 0.43, '100': 0.37},
			{type: '0.8', '30': 0.45, '50': 0.42, '80': 0.39, '100': 0.32},
			{type: '1', '30': 0.41, '50': 0.38, '80': 0.33, '100': 0.26}
		];
		var matrixWithData = [
			{type: '0.3', '30': 0.54, '50': 0.49, '80': 0.42, '100': 0.22},
			{type: '0.5', '30': 0.49, '50': 0.47, '80': 0.31, '100': 0.20},
			{type: '0.8', '30': 0.44, '50': 0.41, '80': 0.29, '100': 0.18},
			{type: '1', '30': 0.41, '50': 0.33, '80': 0.24, '100': 0.15}
		];
		var matrixDiffData = [];
		for (var i = 0; i < matrixWithoutData.length; i++) {
			var dataRow = {type: matrixWithoutData[i].type};
			for (var ind in matrixWithoutData[i]) {
				if (ind !== 'type') {
					dataRow[ind] = matrixWithoutData[i][ind] - matrixWithData[i][ind];
				}
			}
			matrixDiffData.push(dataRow);
		}
		
		var colors = ['rgba(252,141,89,0.5)','rgba(254,224,139,0.5)','rgba(255,255,191,0.5)','rgba(217,239,139,0.5)','rgba(145,207,96,0.5)'];
		var colorScale = d3.scale.threshold()
			.domain([0.24, 0.32, 0.40, 0.48])
			.range(colors);
		var diffColorScale = d3.scale.threshold()
			.domain([0, 0.025, 0.045, 0.095])
			.range(colors);
		
		var currAttr = 'diff';
		var updateMatrix = function(data) {
			var rows = d3.select('.output-matrix-table tbody').selectAll('tr')
				.data(data);
			var newRows = rows.enter().append('tr');
			
			var cells = rows.selectAll('td')
				.data(function(d) { return ['type', '30', '50', '80', '100'].map(function(dd) { return d[dd]; }); });
			cells.enter().append('td');
			
			rows.selectAll('td')
				.classed('success', function(d, i) { if (i > 0) return currAttr === 'diff' && d > 0; })
				.classed('danger', function(d, i) { if (i > 0) return currAttr === 'diff' && d < 0; })
				.style('background-color', function(d, i) {
					if (i > 0) {
						return (currAttr === 'diff') ? diffColorScale(d) : colorScale(d);
					}
				})
				.text(function(d, i) {
					if (i === 0) return Util.percentize(d);
					else return (currAttr === 'diff') ? d3.format('+%')(d) : Util.percentize(d);
				});	

			// add black border around relevant cell
			d3.select('.output-matrix-table tbody tr:nth-child(3) td:nth-child(4)')
				.style('font-weight', '600')
				.append('div').attr('class', 'selected-border-box');
		};
		updateMatrix(matrixDiffData);
		$('.matrix-attr-btn-group .btn').on('click', function() {
			$(this).addClass('active')
				.siblings().removeClass('active');
				
			currAttr = $(this).attr('name');
			if (currAttr === 'diff') updateMatrix(matrixDiffData);
			else if (currAttr === 'separate') updateMatrix(matrixWithoutData);
			else if (currAttr === 'integrated') updateMatrix(matrixWithData);
		});
		
		
		
		// back to inputs button
		$('.input-back-button').click(function() { hasher.setHash(''); });
	};
	
	App.initialize();
	Routing.precompileTemplates();	
	Routing.initializeRoutes();	
})();