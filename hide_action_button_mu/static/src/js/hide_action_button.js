odoo.define("hide_action_button_mu.hide_action_button", function(require) {
	"use strict";
		
	var Sidebar = require('web.Sidebar');
	
	Sidebar.include({
		add_items: function (sectionCode, items) {
				var self = this;
				var _super = this._super;

				var new_items = items;
				
				if (sectionCode === "other" && odoo.session_info.isActionDisabled) {
					new_items = []				    				    
				}
				if (new_items.length > 0) {
					console.log(new_items);
				    _super.call(self, sectionCode, new_items);
				}
		},		
	});
});

    
