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
		valText = Util.percentize(val);
	}
	input.val(valText);
	return val;
};
