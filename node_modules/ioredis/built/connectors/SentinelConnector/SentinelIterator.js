"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function isSentinelEql(a, b) {
    return ((a.host || '127.0.0.1') === (b.host || '127.0.0.1')) &&
        ((a.port || 26379) === (b.port || 26379));
}
class SentinelIterator {
    constructor(sentinels) {
        this.sentinels = sentinels;
        this.cursor = 0;
    }
    hasNext() {
        return this.cursor < this.sentinels.length;
    }
    next() {
        return this.hasNext() ? this.sentinels[this.cursor++] : null;
    }
    reset(moveCurrentEndpointToFirst) {
        if (moveCurrentEndpointToFirst && this.sentinels.length > 1 && this.cursor !== 1) {
            const remains = this.sentinels.slice(this.cursor - 1);
            this.sentinels = remains.concat(this.sentinels.slice(0, this.cursor - 1));
        }
        this.cursor = 0;
    }
    add(sentinel) {
        for (let i = 0; i < this.sentinels.length; i++) {
            if (isSentinelEql(sentinel, this.sentinels[i])) {
                return false;
            }
        }
        this.sentinels.push(sentinel);
        return true;
    }
    toString() {
        return `${JSON.stringify(this.sentinels)} @${this.cursor}`;
    }
}
exports.default = SentinelIterator;
