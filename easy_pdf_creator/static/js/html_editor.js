odoo.define('easy_pdf_creator.html_editor', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var Model = require('web.DataModel');
    var common = require('web.form_common');
    var base = require('web_editor.base');
    var editor = require('web_editor.editor');
    var transcoder = require('web_editor.transcoder');
    var widgets = require('web_editor.widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var widget = common.AbstractField.extend(common.ReinitializeFieldMixin);

    function _config() {
        var config = {
            height: 180,
            //selector: ".oe_form_field_html_text textarea",
            browser_spellcheck: true,
            fontsize_formats: "8pt 10pt 12pt 14pt 16pt 18pt 20pt 24pt 36pt",
            plugins: [
                'advlist autolink charmap textcolor',
                'searchreplace code fullscreen emoticons',
                'table paste code hr emoticons codesample wordcount'
            ],
            toolbar: 'insertfile undo redo | styleselect fontselect fontsizeselect | bold italic underline forecolor backcolor | alignleft aligncenter alignright | bullist numlist | outdent indent | odoo_link odoo_media table charmap emoticons codesample hr | fullscreen code ',
            menubar: false,
            extended_valid_elements: "iframe[src|frameborder|style|scrolling|class|width|height|name|align|table]",
            table_default_styles: {width: '100%'},
            setup: function (editor) {

                // Add a new button to call Odoo's LinkDialog
                editor.addButton('odoo_link', {
                    icon: "link",
                    tooltip: "Insert/edit link",
                    onclick: function () {
                        // Get the selection
                        var dom_selection = editor.selection;
                        dom_selection.select();
                        var $selected_node = $(dom_selection.getNode());
                        // Link info
                        var linkinfo = {
                            iniClassName: $selected_node.attr('class'),
                            isNewWindow: $selected_node.attr('target') == '_blank',
                            text: dom_selection.getContent(),
                            url: $selected_node.attr('href')
                        };
                        // Initialize Link Dialog
                        var link_dialog = new widgets.LinkDialog(editor, linkinfo);
                        // Display the Link Dialog
                        link_dialog.appendTo(document.body);
                        // On save
                        link_dialog.on("save", this, function (linkInfo) {
                            // Create the link
                            var $new_link = $("<a>");
                            $new_link.attr({
                                'class': linkInfo.className,
                                'href': linkInfo.url,
                                'target': linkInfo.isNewWindow ? '_blank' : '_self'
                            });
                            $new_link.text(linkInfo.text);
                            // Insert the link the selection
                            editor.insertContent($new_link[0].outerHTML);
                        });
                    },
                    stateSelector: "a[href]"
                });

                // Add a new button to call Odoo's MediaDialog
                editor.addButton("odoo_media", {
                    icon: "image",
                    tooltip: "Insert/edit image",
                    onclick: function () {
                        // Get the selection
                        var dom_selection = editor.selection;
                        dom_selection.select();
                        var selected_node = dom_selection.getNode();
                        // Initialize Media Dialog
                        var media_dialog = new widgets.MediaDialog(null, selected_node);
                        // Display the Media Dialog
                        media_dialog.appendTo(document.body);
                        // On save
                        media_dialog.on("saved", this, function (media) {
                            dom_selection.select();
                        });
                    },
                    stateSelector: "img:not([data-mce-object],[data-mce-placeholder]),figure.image"
                });
            },
            content_css: [
                '/web/static/lib/bootstrap/css/bootstrap.min.css',
                '/web/static/lib/fontawesome/css/font-awesome.css',
                '/web/static/src/less/mimetypes.less.css',
                '/easy_pdf_creator/static/styles/css/tinymce.css'],
            remove_trailing_brs: false,
            verify_html: false
        };
        if (session.debug) {
            //config.toolbar += 'code';
        }
        return config;
    }

    tinymce.baseURL = '/easy_pdf_creator/static/js/lib/tinymce/';
    tinymce.suffix = '.min';
    $('.oe_form_field_html_text textarea').livequery(function () {
        if ($(".modal-content .oe_form_editable").length || !$(".oe_form_readonly").length && !$(".modal-content .oe_form_readonly").length) {
            $(this).each(function () {
                try {
                    $(this).tinymce().remove();
                }
                catch (err) {
                }
                finally {
                    var config = _config();
                    $(this).tinymce(config);
                }
            });
        }
    });


    // Simple FieldTextHTML
    var FieldTextHtmlSimple = widget.extend({
        template: 'web_editor.FieldTextHtmlSimple',
        start: function () {
            var def = this._super.apply(this, arguments);
            this.$translate.remove();
            this.$translate = $();
            return def;
        },
        initialize_content: function () {
            var self = this;
            this.$textarea = this.$("textarea").val(this.get('value') || "<p><br/></p>");
            this.$textarea.css('opacity', 0);

            if (this.get("effective_readonly")) {
                this.$textarea.hide().after('<div class="note-editable"/>');
            } else {
                if (this.field.translate && this.view) {
                    $(QWeb.render('web_editor.FieldTextHtml.button.translate', {'widget': this}))
                        .appendTo(this.$('.note-toolbar'))
                        .on('click', this.on_translate);
                }
            }
            this.$content = this.$('.note-editable:first');

            $(".oe-view-manager-content").on("scroll", function () {
                $('.o_table_handler').remove();
            });

            this._super();
        },
        text_to_html: function (text) {
            // Clean text before converting to HTML
            var value = text || "";
            if (value.match(/^\s*$/)) {
                value = '<p><br/></p>';
            } else {
                value = "<p>" + value.split(/<br\/?>/).join("<br/></p><p>") + "</p>";
                value = value.replace(/<p><\/p>/g, '').replace('<p><p>', '<p>').replace('</p></p>', '</p>');
            }
            return value;
        },
        render_value: function () {
            // Render field's HTML to the editor
            var value = this.get('value');
            this.$textarea.val(value || '');
            this.$content.html(this.text_to_html(value));
        },
        is_false: function () {
            return !this.get('value') || this.get('value') === "<p><br/></p>" || !this.get('value').match(/\S/);
        },
        before_save: function () {
            // Before saving the record, set the HTML field value to the content of TinyMCE
            if (!this.get("effective_readonly")) {
                var $tinymce_body = tinymce.get(this.$textarea[0].id).$("#tinymce");
                if (this.options['style-inline']) {
                    // Convert class to inline styles for email use
                    transcoder.class_to_style($tinymce_body);
                    // Convert font-awesome to images
                    transcoder.font_to_img($tinymce_body);
                }
                // Set the value of field
                this.internal_set_value($tinymce_body.html());
            }
        },
        commit_value: function () {
            this.before_save();
        },
        destroy_content: function () {
            $(".oe-view-manager-content").off("scroll");
            this.$textarea.destroy();
            this._super();
        }
    });

    // FieldTextHTML
    var FieldTextHtml = widget.extend({
        template: 'web_editor.FieldTextHtml',
        willStart: function () {
            var self = this;
            return new Model('res.lang').call("search_read", [[['code', '!=', 'en_US']], ["name", "code"]]).then(function (res) {
                self.languages = res;
            });
        },
        start: function () {
            var self = this;

            this.callback = _.uniqueId('FieldTextHtml_');
            window.odoo[this.callback + "_editor"] = function (EditorBar) {
                setTimeout(function () {
                    self.on_editor_loaded(EditorBar);
                }, 0);
            };
            window.odoo[this.callback + "_content"] = function (EditorBar) {
                self.on_content_loaded();
            };
            window.odoo[this.callback + "_updown"] = null;
            window.odoo[this.callback + "_downup"] = function (value) {
                self.internal_set_value(value);
                self.trigger('changed_value');
                self.resize();
            };

            // init jqery objects
            this.$iframe = this.$el.find('iframe');
            this.document = null;
            this.$body = $();
            this.$content = $();

            this.$iframe.css('min-height', 'calc(100vh - 360px)');

            // init resize
            this.resize = function resize() {
                if (self.get('effective_readonly')) {
                    return;
                }
                if ($("body").hasClass("o_form_FieldTextHtml_fullscreen")) {
                    self.$iframe.css('height', (document.body.clientHeight - self.$iframe.offset().top) + 'px');
                } else {
                    self.$iframe.css("height", (self.$body.find("#oe_snippets").length ? 500 : 300) + "px");
                }
            };
            $(window).on('resize', self.resize);

            var def = this._super.apply(this, arguments);
            this.$translate.remove();
            this.$translate = $();
            return def;
        },
        get_url: function (_attr) {
            var src = this.options.editor_url ? this.options.editor_url + "?" : "/web_editor/field/html?";
            var datarecord = this.view.get_fields_values();

            var attr = {
                'model': this.view.model,
                'field': this.name,
                'res_id': datarecord.id || '',
                'callback': this.callback
            };
            _attr = _attr || {};

            if (this.options['style-inline']) {
                attr.inline_mode = 1;
            }
            if (this.options.snippets) {
                attr.snippets = this.options.snippets;
            }
            if (!this.get("effective_readonly")) {
                attr.enable_editor = 1;
            }
            if (this.field.translate) {
                attr.translatable = 1;
            }
            if (session.debug) {
                attr.debug = 1;
            }

            attr.lang = attr.enable_editor ? 'en_US' : this.session.user_context.lang;

            for (var k in _attr) {
                attr[k] = _attr[k];
            }

            for (var k in attr) {
                if (attr[k] !== null) {
                    src += "&" + k + "=" + (_.isBoolean(attr[k]) ? +attr[k] : attr[k]);
                }
            }

            delete datarecord[this.name];
            src += "&datarecord=" + encodeURIComponent(JSON.stringify(datarecord));

            return src;
        },
        initialize_content: function () {
            this.$el.closest('.modal-body').css('max-height', 'none');
            this.$iframe = this.$el.find('iframe');
            this.document = null;
            this.$body = $();
            this.$content = $();
            this.editor = false;
            window.odoo[this.callback + "_updown"] = null;
            this.$iframe.attr("src", this.get_url());
        },
        on_content_loaded: function () {
            var self = this;
            this.document = this.$iframe.contents()[0];
            this.$body = $("body", this.document);
            this.$content = this.$body.find("#editable_area");
            this._toggle_label();
            this.lang = this.$iframe.attr('src').match(/[?&]lang=([^&]+)/);
            this.lang = this.lang ? this.lang[1] : this.view.dataset.context.lang;
            this._dirty_flag = false;
            this.render_value();
            setTimeout(function () {
                self.add_button();
                setTimeout(self.resize, 0);
            }, 0);
        },
        on_editor_loaded: function (EditorBar) {
            var self = this;
            this.editor = EditorBar;
            if (this.get('value') && window.odoo[self.callback + "_updown"] && !(this.$content.html() || "").length) {
                this.render_value();
            }
            setTimeout(function () {
                setTimeout(self.resize, 0);
            }, 0);
        },
        add_button: function () {
            var self = this;
            var $to = this.$body.find("#web_editor-top-edit, #wrapwrap").first();

            $(QWeb.render('web_editor.FieldTextHtml.translate', {'widget': this}))
                .appendTo($to)
                .on('change', 'select', function () {
                    var lang = $(this).val();
                    var edit = !self.get("effective_readonly");
                    var trans = lang !== 'en_US';
                    self.$iframe.attr("src", self.get_url({
                        'edit_translations': edit && trans,
                        'enable_editor': edit && !trans,
                        'lang': lang
                    }));
                });

            $(QWeb.render('web_editor.FieldTextHtml.fullscreen'))
                .appendTo($to)
                .on('click', '.o_fullscreen', function () {
                    $("body").toggleClass("o_form_FieldTextHtml_fullscreen");
                    var full = $("body").hasClass("o_form_FieldTextHtml_fullscreen");
                    self.$iframe.parents().toggleClass('o_form_fullscreen_ancestor', full);
                    self.resize();
                });

            this.$body.on('click', '[data-action="cancel"]', function (event) {
                event.preventDefault();
                self.initialize_content();
            });
        },
        render_value: function () {
            if (this.lang !== this.view.dataset.context.lang || this.$iframe.attr('src').match(/[?&]edit_translations=1/)) {
                return;
            }
            var value = (this.get('value') || "").replace(/^<p[^>]*>(\s*|<br\/?>)<\/p>$/, '');
            if (!this.$content) {
                return;
            }
            if (!this.get("effective_readonly")) {
                if (window.odoo[this.callback + "_updown"]) {
                    window.odoo[this.callback + "_updown"](value, this.view.get_fields_values(), this.name);
                    this.resize();
                }
            } else {
                this.$content.html(value);
                if (this.$iframe[0].contentWindow) {
                    this.$iframe.css("height", (this.$body.height() + 20) + "px");
                }
            }
        },
        is_false: function () {
            return this.get('value') === false || !this.$content.html() || !this.$content.html().match(/\S/);
        },
        before_save: function () {
            if (this.lang !== 'en_US' && this.$body.find('.o_dirty').length) {
                this.internal_set_value(this.view.datarecord[this.name]);
                this._dirty_flag = false;
                return this.editor.save();
            } else if (this._dirty_flag && this.editor && this.editor.buildingBlock) {
                this.editor.buildingBlock.clean_for_save();
                this.internal_set_value(this.$content.html());
            }
        },
        destroy: function () {
            $(window).off('resize', self.resize);
            delete window.odoo[this.callback + "_editor"];
            delete window.odoo[this.callback + "_content"];
            delete window.odoo[this.callback + "_updown"];
            delete window.odoo[this.callback + "_downup"];
        }
    });

    core.form_widget_registry
        .add('html', FieldTextHtmlSimple)
        .add('html_frame', FieldTextHtml);

});
