var Util = {};

Util.comma = d3.format(',f');
Util.decimalize = d3.format('.2f');
Util.percentize = d3.format('%'); // divides by 100 and adds a percentage symbol

// converts a number in string format into a float
Util.strToFloat = function(str) {
	if (typeof str !== 'string') return str;
	return parseFloat(str.replace(/[^\d\.\-]/g, ""));
};

// formats the value for an input
Util.formatInputVal = function(input) {
	input = $(input);
	var val = Util.strToFloat(input.val());
	var valText = Util.comma(val);
	if (input.hasClass('percent-input')) {
		val /= 100;
		if (isNaN(val) || val < 0) val = 0;
		else if (val > 100) val = 100;
		valText = Util.percentize(val);
	}
	input.val(valText);
	return val;
};

// get unique values from an array
Util.getUnique = function(array) {
	var result = [];
	for (var i = 0; i < array.length; i++) {
		if (result.indexOf(array[i]) === -1) result.push(array[i]);
	}
	return result;
};
