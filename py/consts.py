SCRIPT_PHOLDER = rb'/*__ACTUAL_SCRIPT_CONTENT_PLACEHOLDER__*/'
SCRIPT_TEMPL = rb'''
return await (async ()=>{  // IIAFE
const communicate = (()=>{
let __webkit = window.webkit;
function __postmsg(x, channel) {
    window.webkit = __webkit;
    const ret = window.webkit.messageHandlers[channel].postMessage(x);
    __webkit = window.webkit;
    window.webkit = undefined;
    return ret;
}
Object.entries({
    trace: 0,  // TRACE
    debug: 1,  // DIAG
    log: 2,  // INFO
    info: 2,  // INFO
    warn: 3,  // WARN
    assert: 4,  // ASSERT
    error: 5,  // ERR
}).forEach(([fn, logType])=>{
    console[fn] = function() {
        __postmsg({logType, argsArr: Array.from(arguments)}, 'wkjs_log');
    };
});
window.webkit = undefined;
return x=>__postmsg(x, 'wkjs_com');
})();
/*__ACTUAL_SCRIPT_CONTENT_PLACEHOLDER__*/
})();
'''
