var App = App || {};

(function() {
	App.initInput = function() {
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
			var valid = true;
			if ($(this).attr('name') === 'pop-age') valid = validatePopAgeSum();
			
			if (valid) {
				var contents = $(this).parent().parent();
				contents.slideUp();
				contents.parent().next('.input-section').find('.input-subsection, .next-button-container').slideDown();
			}
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
				$('.pop-age-table input').css('background-color', 'white');
				return true;
			} else {
				$('.pop-age-warning').slideDown();
				$('.pop-age-table input').css('background-color', '#ffdbdb');
				return false;
			}
		};
		var validatePopAgeSum = function() {
			var valid = checkPopAgeSum();
			if (!valid) noty({layout: 'center', type: 'warning', text: '<b>Warning!</b><br>Age distributions must sum to 100%!'});
			return valid;
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
		$('.input-submit-button').click(function() {
			var valid = validatePopAgeSum();
			if (valid) hasher.setHash('output');
		});
		
		
		// slide open first input section
		$('.input-section[name="pop-age"]').find('.input-subsection, .next-button-container').slideDown();
	};
})();
