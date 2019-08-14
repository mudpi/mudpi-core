"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const net_1 = require("net");
const tls_1 = require("tls");
const utils_1 = require("../utils");
const AbstractConnector_1 = require("./AbstractConnector");
function isIIpcConnectionOptions(value) {
    return value.path;
}
exports.isIIpcConnectionOptions = isIIpcConnectionOptions;
class StandaloneConnector extends AbstractConnector_1.default {
    constructor(options) {
        super();
        this.options = options;
    }
    connect(callback, _) {
        const { options } = this;
        this.connecting = true;
        let connectionOptions;
        if (isIIpcConnectionOptions(options)) {
            connectionOptions = {
                path: options.path
            };
        }
        else {
            connectionOptions = {};
            if (options.port != null) {
                connectionOptions.port = options.port;
            }
            if (options.host != null) {
                connectionOptions.host = options.host;
            }
            if (options.family != null) {
                connectionOptions.family = options.family;
            }
        }
        if (options.tls) {
            Object.assign(connectionOptions, options.tls);
        }
        process.nextTick(() => {
            if (!this.connecting) {
                callback(new Error(utils_1.CONNECTION_CLOSED_ERROR_MSG));
                return;
            }
            let stream;
            try {
                if (options.tls) {
                    stream = tls_1.connect(connectionOptions);
                }
                else {
                    stream = net_1.createConnection(connectionOptions);
                }
            }
            catch (err) {
                callback(err);
                return;
            }
            this.stream = stream;
            callback(null, stream);
        });
    }
}
exports.default = StandaloneConnector;
