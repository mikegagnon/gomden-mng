"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var DEFAULT_GOMDEN_CONFIG = {};

var Gomden = function () {
    function Gomden(config) {
        _classCallCheck(this, Gomden);

        if (!config) {
            config = {};
        }
        this.config = $.extend({}, DEFAULT_GOMDEN_CONFIG, config);
    }

    _createClass(Gomden, [{
        key: "launch",
        value: function launch() {
            this.loadPage();
        }
    }, {
        key: "loadPage",
        value: function loadPage() {
            var url = this.config.getPageUrl;
            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadPageSuccess(data);
            }).fail(function () {
                console.error("loadPage failed");
            });
        }
    }, {
        key: "loadPageSuccess",
        value: function loadPageSuccess(data) {
            console.log(data);

            $("#gomden-container").text(data.page.content);
        }
    }, {
        key: "launchEdit",
        value: function launchEdit() {
            this.loadEditPage();
        }
    }, {
        key: "loadEditPage",
        value: function loadEditPage() {
            var url = this.config.getPageUrl;
            var THIS = this;

            $.get(url).success(function (data) {
                THIS.loadEditPageSuccess(data);
            }).fail(function () {
                console.error("loadPage failed");
            });
        }
    }, {
        key: "loadEditPageSuccess",
        value: function loadEditPageSuccess(data) {
            $("#gomden-container").text("Edit: " + data.page.content);
        }
    }]);

    return Gomden;
}();