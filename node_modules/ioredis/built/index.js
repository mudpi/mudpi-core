"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports = module.exports = require('./redis');
var redis_errors_1 = require("redis-errors");
exports.ReplyError = redis_errors_1.ReplyError;
exports.Cluster = require('./cluster').default;
exports.Command = require('./command').default;
exports.ScanStream = require('./ScanStream').default;
exports.Pipeline = require('./pipeline').default;
const PromiseContainer = require('./promiseContainer');
Object.defineProperty(exports, 'Promise', {
    get() {
        return PromiseContainer.get();
    },
    set(lib) {
        PromiseContainer.set(lib);
    }
});
exports.print = function (err, reply) {
    if (err) {
        console.log('Error: ' + err);
    }
    else {
        console.log('Reply: ' + reply);
    }
};
