// alert("Loaded!");
// console.log("loaded again!");
odoo.define('stock_xls_report.retain_wizard', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var _t = core._t;
var ActionManager = require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');
var session = require('web.session');

var _t = core._t;
var _lt = core._lt;

// var ControlPanelMixin = require('web.ControlPanelMixin');
// 
// var utils = require('web.utils');
// var CrashManager = require('web.CrashManager');
// 
// var Dialog = require('web.Dialog');
// var formats = require('web.formats');
// var FormView = require('web.FormView');
// var ListView = require('web.ListView');
// var Model = require('web.Model');
 var pyeval = require('web.pyeval');
// var web_client = require('web.web_client');
// var parse_value = require('web.web_client');
// var Widget = require('web.Widget');
// var session = require('web.session');
// 
// var FieldMany2One = core.form_widget_registry.get('many2one');
// var FieldChar = core.form_widget_registry.get('char');
// var FieldFloat = core.form_widget_registry.get('float');
// 
// 




// var QWeb = core.qweb;
// var bus = core.bus;
// ActionManager.include({
// ir_actions_report_xml_no_close: function(action, options) {
// debugger;
//         var self = this;
//         framework.blockUI();
//         action = _.clone(action);
//         var eval_contexts = ([session.user_context] || []).concat([action.context]);
//         action.context = pyeval.eval('contexts',eval_contexts);
// 
//         // iOS devices doesn't allow iframe use the way we do it,
//         // opening a new window seems the best way to workaround
//         if (navigator.userAgent.match(/(iPod|iPhone|iPad)/)) {
//             var params = {
//                 action: JSON.stringify(action),
//                 token: new Date().getTime()
//             };
//             var url = self.session.url('/web/report', params);
//             framework.unblockUI();
//             $('<a href="'+url+'" target="_blank"></a>')[0].click();
//             return;
//         }
//         var c = crash_manager;
//         return $.Deferred(function (d) {
//             self.session.get_file({
//                 url: '/web/report',
//                 data: {action: JSON.stringify(action)},
//                 complete: framework.unblockUI,
//                 success: function(){
//                     if (!self.dialog) {
//                         options.on_close();
//                     }
// //                     self.dialog_stop();
//                     d.resolve();
//                 },
//                 error: function () {
//                     c.rpc_error.apply(c, arguments);
//                     d.reject();
//                 }
//             });
//         });
//     },
//   });  
// });    
    
ActionManager.include({
ir_actions_report_xml: function(action, options) {
// debugger;
        var self = this;
        console.log("my fuction running");
//         return self._super(action,options);
        framework.blockUI();
        action = _.clone(action);
        var eval_contexts = ([session.user_context] || []).concat([action.context]);
        action.context = pyeval.eval('contexts',eval_contexts);

        // iOS devices doesn't allow iframe use the way we do it,
        // opening a new window seems the best way to workaround
        if (navigator.userAgent.match(/(iPod|iPhone|iPad)/)) {
            var params = {
                action: JSON.stringify(action),
                token: new Date().getTime()
            };
            var url = self.session.url('/web/report', params);
            framework.unblockUI();
            $('<a href="'+url+'" target="_blank"></a>')[0].click();
            return;
        }
        var c = crash_manager;
        return $.Deferred(function (d) {
            self.session.get_file({
                url: '/web/report',
                data: {action: JSON.stringify(action)},
                complete: framework.unblockUI,
                success: function(){
                    if (!self.dialog) {
                        options.on_close();
                    }
                    // for stock excel report
                    if (action.report_name != "export_stockinfo_xls.stock_report_xls.xlsx"){
                       self.dialog_stop();
                    }
                    d.resolve();
                },
                error: function () {
                    c.rpc_error.apply(c, arguments);
                    d.reject();
                }
            });
        });
    },
  });  
});    
    
    
