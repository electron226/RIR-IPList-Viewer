$(function() {
	// jQuery Tools
	$("ul.tabs").tabs("div.panes > div");

	// jQuery
	$("button#open").click(function() {
		$("div#view").show("slow");
	});
	$("button#close").click(function() {
		$("div#view").hide("slow");
	});
})
