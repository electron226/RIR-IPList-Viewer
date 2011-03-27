// jQuery
$(function() {
	$("button#open").click(function() {
		$("div#view").show("slow");
	});
	$("button#close").click(function() {
		$("div#view").hide("slow");
	});
})
