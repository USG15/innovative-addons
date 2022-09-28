odoo.define('stock_xls_report.multi_action', function(require) {
    "use strict";

    var ActionManager = require("web.ActionManager");

    ActionManager.include({
        /**
         * Intercept action handling to detect extra action type
         * @override
         */
        // debugger;
        _handleAction: function(action, options) {
            if (action.type === "ir.actions.act_multi") {
                return this._executeMultiAction(action, options);
            }
            return this._super.apply(this, arguments);
        },

        /**
         * Handle 'ir.actions.act_multi' action
         * @param {Object} action see _handleAction() parameters
         * @param {Object} options see _handleAction() parameters
         * @returns {$.Promise}
         */
        _executeMultiAction: function(action, options) {
//             const self = this;
            var self= this;

//             return action.actions
//                 .map(item => {
                debugger;
                return action.actions.map(item => {
                    return () => {
                        return self._handleAction(item, options);
                    };
                })
                .reduce((prev, cur) => {
                    return prev.then(cur);
                }, Promise.resolve());
        },
    });
});