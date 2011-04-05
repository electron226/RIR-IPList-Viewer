$(function() {
	// jQuery Tools
	$("ul.tabs").tabs("div.panes > div.page");

	$("#accordion").tabs("#accordion div.pane", {tabs: 'h2', effect:"slide", initialIndex: null});
	$.tools.tabs.addEffect("slide", function(i, done) {
		// 1. upon hiding, the active pane has a ruby background color
		this.getPanes().slideUp().css({backgroundColor: "#b8128f"});

		// 2. after a pane is revealed,  its background is set to its original color (transparent)
		this.getPanes().eq(i).slideDown(function() {
			$(this).css({backgroundColor: 'transparent'});

			// the supplied callback must be called after hte effect has finished its job
			done.call();
		});
	});
});
