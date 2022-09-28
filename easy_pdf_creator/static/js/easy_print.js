odoo.define('easy_pdf_creator.SidebarInherit', function (require) {
    'use strict';
    // ------
    var Sidebar = require('web.Sidebar');
    var Model = require('web.Model');
    var CrashManager = require('web.CrashManager');

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    // SideBar inherit
    Sidebar.include({
        start: function() {
            var self = this;
            this._super(this);
            // Custom add items
            this.add_items('print', [
                {   label: _t('EasyPrint'),
                    callback: self.on_click_easy_print, // function
                    classname: 'oe_easy_print' },
            ]);
            // -----
        },
        // Event
        on_click_easy_print: function(item) {
            var view = this.getParent()
            launch_easy_print(this, view); // function
        },
    });

    // to Python - Check pdf template
    function launch_easy_print(self, view) {
        var self = this;
        var res_model = view['model'];
        var res_id = view['datarecord'].id;
        var template_id;
        return new Model('pdf.template.generator').call("search", [[
                ["model_id.model","=",res_model],
                ["name","=","default"] 
                ]])
            .done(function (template) {
                console.log('-----temp-----', template, res_model, res_id);
                if(template != false){
                    return new Model("pdf.template.generator")
                        .call("print_template", [ template[0], res_id])
                            .then(function(result){
                                view.do_action(result);
                        });
                }else{
                    // Not found, Warning
                    new CrashManager().show_warning({data: {
                        exception_type: _t("Warning"),
                        message: _t("Not found template!, must be template name 'default'")
                    }});
                }

            });
    }
});
