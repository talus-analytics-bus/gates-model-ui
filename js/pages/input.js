var App = App || {};

(function() {
	App.initInput = function() {
		if (App.inputs !== null) setExistingInputValues();
		
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
				var mainContents = $(this).parent().parent();
				var contents = mainContents.find('.input-subsection, .next-button-container');
				contents.slideUp();
				mainContents.parent().next('.input-section').find('.input-subsection, .next-button-container').slideDown();
			}
		});
		
		
		/* --------------------- Population Section ----------------------- */
		var popAgeData = [
			{age: '0-4', value: App.inputs ? App.inputs.pop1 : 0.20},
			{age: '5-15', value: App.inputs ? App.inputs.pop2 : 0.34},
			{age: '16+', value: App.inputs ? App.inputs.pop3 : 0.46},
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
			if (!valid) noty({text: '<b>Warning!</b><br>Age distributions must sum to 100%!'});
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
		
		
		/* --------------------- Schisto Section ----------------------- */
		// picking a schistosomiasis prevalence
		$('.schisto-prevalence').on('change', function() {
			var val = Math.round(Util.strToFloat($(this).val()));
			if (isNaN(val)) {
				noty({text: '<b>Error!</b><br>Please select a valid number for schistosomiasis prevalence.'});
				$(this).val(Util.percentize(0.45));
			} else if (val <= 0) {
				noty({text: '<b>Warning!</b><br>The percentage for schistosomiasis prevalence must be <b>greater than 0%</b>.'});
				$(this).val(Util.percentize(0.01));
			} else if (val > 100) {
				noty({text: '<b>Warning!</b><br>The maximum percentage for schistosomiasis prevalence is <b>100%</b>.'});
				$(this).val(Util.percentize(1));
			} else {
				$(this).val(Util.percentize(val/100));
			}
		});
		
		// multiselect for age range
		$('.schisto-age-select').multiselect();
		
		
		/* --------------------- Malaria Section ----------------------- */
		// malaria transmission pattern
		$('.malaria-timing-select').on('change', function() {
			if ($(this).val() === 'seasonal') $('.malaria-month-container').slideDown();
			else $('.malaria-month-container').slideUp();
		});
		$('.malaria-month-select').multiselect();
		
		
		// checkboxes for IRS and ITN
		$('.irs-checkbox').on('change', function() { irsChange(); });
		$('.irs-checkbox-label').on('click', function() {
			$('.irs-checkbox').prop('checked', !$('.irs-checkbox').is(':checked'));
			irsChange();
		});
		var irsChange = function() {
			$('.irs-true-contents').slideToggle();
			updateDistributionBlock();
		};
		$('.itn-checkbox').on('change', function() { itnChange(); });
		$('.itn-checkbox-label').on('click', function() {
			$('.itn-checkbox').prop('checked', !$('.itn-checkbox').is(':checked'));
			itnChange();
		});
		var itnChange = function() {
			$('.itn-true-contents').slideToggle();
			updateDistributionBlock();
		};
		var updateDistributionBlock = function() {
			var show = $('.irs-checkbox').is(':checked') && $('.itn-checkbox').is(':checked');
			if (show) $('.input-subsection[name="distribution-strategy"]').slideDown();
			else $('.input-subsection[name="distribution-strategy"]').slideUp();
		};
		
		
		/* --------------------- Submission ----------------------- */
		// submit button
		$('.input-submit-button').click(function() {
			// define user inputs
			var inputs = {
				n_people: 2000,
				pop1: Util.strToFloat($('.pop-age-table tbody tr:first-child input').val()) / 100, // age distribution for under 5
				pop2: Util.strToFloat($('.pop-age-table tbody tr:nth-child(2) input').val()) / 100, // age distribution for 5-15
				pop3: Util.strToFloat($('.pop-age-table tbody tr:nth-child(3) input').val()) / 100, // age distribution for 16+
				schisto_prevalence: Util.strToFloat($('.schisto-prevalence').val()) / 100, // schistosomiasis prevalence percentage
				schisto_coverage: Util.strToFloat($('.schisto-coverage-select').val()), // target % coverage for schisto
				schisto_age_range: $('.schisto-age-select').val(), // schisto age range
				schisto_month_num: $('.schisto-month-select').val(), // schisto distribution time
				malaria_timing: $('.malaria-timing-select').val(), // malaria timing
				malaria_peak_month_num: $('.malaria-month-select').val(), // array of malaria peak transmission month numbers (1-Jan, 2-Feb, etc.)
				malaria_rate: Util.strToFloat($('.malaria-trans-rate-select').val()), // malaria transmission rate
				irs: $('.irs-checkbox').is(':checked') ? 1 : 0, // whether IRS is an option
				irs_coverage: Util.strToFloat($('.irs-coverage-select').val()), // IRS target % coverage
				irs_month_num: $('.irs-month-select').val(), // IRS distribution month number (1-Jan, 2-Feb, etc.)
				itn: $('.itn-checkbox').is(':checked') ? 1 : 0, // whether ITN is an option
				itn_coverage: Util.strToFloat($('.itn-coverage-select').val()), // ITN target % coverage
				itn_month_num: $('.itn-month-select').val() // ITN distribution month number (1-Jan, 2-Feb, etc.)
			};


			/* -------- Validation -------- */
			// validate that the population age distribution sums to 100%
			if (validatePopAgeSum() === false) {
				noty({text: '<b>Error!</b><br>Please make sure the age distribution in the population section adds up to 100%!'});
				return false;
			}
			
			// validate that an age range was chosen
			if (inputs.schisto_age_range === null) {
				noty({
					text: '<b>Error!</b><br>Please select an age range for praziquantel ' +
						'mass drug administration under the schistosomiasis section.'
				});
				return false;
			}
			
			// validate that either IRS or ITN was chosen
			if (!inputs.irs && !inputs.itn) {
				noty({text: '<b>Error!</b><br>Please select either <b>IRS</b> or <b>ITN</b> as an option for treatment of malaria.'});
				return false;
			}

			// check that more than 8 months havent been chosen
			if (inputs.malaria_peak_month_num.length > 8) {
				noty({
					text: '<b>Error!</b><br>There may only be up to <b>8</b> peak transmission months for malaria.' + 
						'<br>There are currently <b>' + inputs.malaria_peak_month_num.length + '</b> months chosen.'
				});
				return false;
			}
			/* -------- -------- --------*/
			
			
			// validation completed, save inputs
			App.inputs = inputs;
			
			// define parameters for model runs; one run with integration, one without
			var inputsWithIntegration = Util.copyObject(App.inputs);
			inputsWithIntegration.use_integration = 1;
			
			var inputsWithoutIntegration = Util.copyObject(App.inputs);
			inputsWithoutIntegration.use_integration = 0;
			
			// run model twice, save outputs, redirect to output page
			queue()
				.defer(App.runModel, inputsWithIntegration)
				.defer(App.runModel, inputsWithoutIntegration)
				.await(function(error, outputWith, outputWithout) {
					if (error) {
						console.log('failed to complete all model runs');
						console.log(error);
						noty({type: 'alert', text: '<b>Error!</b><br>There was an error running the model. Please contact the developers.'});
						return false;
					}
					App.outputs = {
						'integrated': outputWith,
						'separate': outputWithout
					};
					
					// set cookies
					App.setCookie('inputs', App.inputs);
					App.setCookie('outputs', App.outputs);
					
					hasher.setHash('output');
				});
		});
		
		
		// slide open first input section
		$('.input-section[name="pop-age"]').find('.input-subsection, .next-button-container').slideDown();
	};
	
	var setExistingInputValues = function() {
		// set inputs in schisto section
		$('.schisto-coverage-select').val(String(App.inputs.schisto_coverage));
		$('.schisto-age-select').val(App.inputs.schisto_age_range);
		$('.schisto-month-select').val(App.inputs.schisto_month_num);
		
		// set inputs in malaria section
		$('.malaria-timing-select').val(App.inputs.malaria_timing);
		if (App.inputs.malaria_timing === 'constant') $('.malaria-month-container').hide();		
		$('.malaria-month-select').val(App.inputs.malaria_peak_month_num);
		$('.malaria-trans-rate-select').val(App.inputs.malaria_rate);
		
		$('.irs-checkbox').prop('checked', App.inputs.irs);
		if (!App.inputs.irs) $('.irs-true-contents').hide();
		$('.irs-coverage-select').val(App.inputs.irs_coverage);
		$('.irs-month-select').val(App.inputs.irs_month_num);
		
		$('.itn-checkbox').prop('checked', App.inputs.itn);
		if (!App.inputs.itn) $('.itn-true-contents').hide();
		$('.itn-coverage-select').val(App.inputs.itn_coverage);
		$('.itn-month-select').val(App.inputs.itn_month_num);
	};
})();
