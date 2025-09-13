HTML = rb'''<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>'''
HOST = rb'''https://www.youtube.com/robots.txt'''
SCRIPT = rb'''
return await (async ()=>{  // IIAFE
const wrapResult = x=>{
    Object.defineProperty(x, 'computed', {
        get() { return this._value * 2; },
        set(v) { this._value = v / 2; },
        enumerable: true
    });
    x._value = 30;
    return x._self_ = x,
    x.dt = new Date,
    x.u8arr = new Uint8Array(3, 46, 7),
    x.carr = [[7, undefined],[3,7],[4,2],[8,0]],
    x.carr[0][1] = x.carr,
    x.map = new Map(x.carr),
    x.nan = NaN,
    x.inf = Infinity,
    x.ninf = -Infinity,
    x.nzr = -0,
    x._bstr = 'a\u0000\n\tbx',
    x.bint = 123456789012345678901234567890n,
    x.sym = Symbol('I'),
    x.si = Symbol.iterator,
    x.ab = new ArrayBuffer(8),
    x.set = new Set([3, 5, 2]),
    x.re = /\s*\d+\s*/gi,
    x.wm = new WeakMap,
    x.ws = new WeakSet,
    x.__proto__ = {in: 32},
    x;
};
try {
// pot for browser, navigate to https://www.youtube.com/robots.txt first
const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko)';
const GOOG_API_KEY = 'AIzaSyDyT5W0Jh49F30Pqqtyfdf7pDLFKLJoAnw';
const REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo'
const YT_BASE_URL = 'https://www.youtube.com';
const GOOG_BASE_URL = 'https://jnn-pa.googleapis.com';

function buildURL(endpointName, useYouTubeAPI) {
    return `${useYouTubeAPI ? YT_BASE_URL : GOOG_BASE_URL}/${useYouTubeAPI ? 'api/jnn/v1' : '$rpc/google.internal.waa.v1.Waa'}/${endpointName}`;
}

function u8ToBase64(u8, base64url = false) {
    const result = btoa(String.fromCharCode(...u8));

    if (base64url) {
        return result
            .replace(/\+/g, '-')
            .replace(/\//g, '_');
    }

    return result;
}

const base64urlToBase64Map = {
    '-': '+',
    _: '/',
    '.': '='
};

const base64urlCharRegex = /[-_.]/g;

function base64ToU8(base64) {
    let base64Mod;

    if (base64urlCharRegex.test(base64)) {
        base64Mod = base64.replace(base64urlCharRegex, function (match) {
            return base64urlToBase64Map[match];
        });
    } else {
        base64Mod = base64;
    }

    base64Mod = atob(base64Mod);

    return new Uint8Array(
        [...base64Mod].map(
            (char) => char.charCodeAt(0)
        )
    );
}

function descramble(scrambledChallenge) {
    const buffer = base64ToU8(scrambledChallenge);
    if (buffer.length)
        return new TextDecoder().decode(buffer.map((b) => b + 97));
}

function parseChallengeData(rawData) {
    let challengeData = [];
    if (rawData.length > 1 && typeof rawData[1] === 'string') {
        const descrambled = descramble(rawData[1]);
        challengeData = JSON.parse(descrambled || '[]');
    } else if (rawData.length && typeof rawData[0] === 'object') {
        challengeData = rawData[0];
    }

    const [messageId, wrappedScript, wrappedUrl, interpreterHash, program, globalName, , clientExperimentsStateBlob] = challengeData;
    const privateDoNotAccessOrElseSafeScriptWrappedValue = Array.isArray(wrappedScript) ? wrappedScript.find((value) => value && typeof value === 'string') : null;
    const privateDoNotAccessOrElseTrustedResourceUrlWrappedValue = Array.isArray(wrappedUrl) ? wrappedUrl.find((value) => value && typeof value === 'string') : null;

    return {
        messageId,
        interpreterJavascript: {
            privateDoNotAccessOrElseSafeScriptWrappedValue,
            privateDoNotAccessOrElseTrustedResourceUrlWrappedValue
        },
        interpreterHash,
        program,
        globalName,
        clientExperimentsStateBlob
    };
}

function isBrowser() {
    const isBrowser = typeof window !== 'undefined'
        && typeof window.document !== 'undefined'
        && typeof window.document.createElement !== 'undefined'
        && typeof window.HTMLElement !== 'undefined'
        && typeof window.navigator !== 'undefined'
        && typeof window.getComputedStyle === 'function'
        && typeof window.requestAnimationFrame === 'function'
        && typeof window.matchMedia === 'function';

    const hasValidWindow = Object.getOwnPropertyDescriptor(globalThis, 'window')?.get?.toString().includes('[native code]') ?? false;

    return isBrowser && hasValidWindow;
}

let headers = {
    'content-type': 'application/json+protobuf',
    'x-goog-api-key': GOOG_API_KEY,
    'x-user-agent': 'grpc-web-javascript/0.1'
};
if (!isBrowser())
    headers['user-agent'] = USER_AGENT;

// fetch challenge
const payload = [REQUEST_KEY];
const resp = await fetch(buildURL('Create', false), {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(payload)
})

if (!resp.ok)
    throw new Error('Failed to fetch challenge');

const rawDataJson = await resp.json();
const bgChallenge = parseChallengeData(rawDataJson);
if (!bgChallenge)
    throw new Error('Could not get challenge');


const interpreterJavascript = bgChallenge.interpreterJavascript.privateDoNotAccessOrElseSafeScriptWrappedValue;

if (interpreterJavascript) {
    new Function(interpreterJavascript)();
} else
    throw new Error('Could not load VM');

const bg = ((vm, program, userInteractionElement) => {
    if (!vm)
        throw new Error('VM not found');
    if (!vm.a)
        throw new Error('VM init function not found');
    let vmFns;
    const vmFunctionsCallback = (asyncSnapshotFunction, shutdownFunction, passEventFunction, checkCameraFunction) => {
        vmFns = { asyncSnapshotFunction, shutdownFunction, passEventFunction, checkCameraFunction };
    };
    const syncSnapshotFunction = vm.a(program, vmFunctionsCallback, true, userInteractionElement, () => {/** no-op */ }, [[], []])[0]
    return { syncSnapshotFunction, vmFns };
})(globalThis[bgChallenge.globalName], bgChallenge.program, bgChallenge.userInteractionElement);

async function snapshot(vmFns, args, timeout = 3000) {
    return await Promise.race([
        new Promise((resolve, reject) => {
            if (!vmFns.asyncSnapshotFunction)
                return reject(new Error('Asynchronous snapshot function not found'));
            vmFns.asyncSnapshotFunction((response) => resolve(response), [
                args.contentBinding,
                args.signedTimestamp,
                args.webPoSignalOutput,
                args.skipPrivacyBuffer
            ]);
        }),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('VM operation timed out')), timeout)
        )
    ]);
}


const webPoSignalOutput = [];
const botguardResponse = await snapshot(bg.vmFns, { webPoSignalOutput });
const generatePayload = [REQUEST_KEY, botguardResponse];

const integrityTokenResponse = await fetch(buildURL('GenerateIT', false), {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(generatePayload)
});
const integrityTokenJson = await integrityTokenResponse.json();
const [integrityToken, estimatedTtlSecs, mintRefreshThreshold, websafeFallbackToken] = integrityTokenJson;

const integrityTokenData = {
    integrityToken,
    estimatedTtlSecs,
    mintRefreshThreshold,
    websafeFallbackToken
};

const minter = await (async (integrityTokenResponse, webPoSignalOutput_) => {
    const getMinter = webPoSignalOutput_[0];

    if (!getMinter)
        throw new Error('PMD:Undefined');

    if (!integrityTokenResponse.integrityToken)
        throw new Error('No integrity token provided');
    const mintCallback = await getMinter(base64ToU8(integrityTokenResponse.integrityToken));

    if (!(mintCallback instanceof Function))
        throw new Error('APF:Failed');
    return async (identifier) => {
        const res = await ((async (identifier) => {
            const result = await mintCallback(new TextEncoder().encode(identifier));
            if (!result)
                throw new Error('YNJ:Undefined');
            if (!(result instanceof Uint8Array))
                throw new Error('ODM:Invalid');
            return result;
        })(identifier));
        return u8ToBase64(res, true);
    };
})(integrityTokenData, webPoSignalOutput);


// // innertube is just for visitor data generation
// import { Innertube } from 'youtubei.js';

// const innertube = await Innertube.create({ user_agent: USER_AGENT, enable_session_cache: false });
// const visitorData = innertube.session.context.client.visitorData || '';

// if (!visitorData)
//     throw new Error('Could not get visitor data');


// console.log(`visitorData(generated with Innertube): ${visitorData}`);
// console.log(`GVS: ${await minter(visitorData)}`);
const pot = await minter(globalThis?.process?.argv[2] || 'dQw4w9WgXcQ');
// return `:.:${document.URL}: ${pot}`;
return wrapResult({result: 'success', debugInfo: [document.URL], data: pot});
//} catch(e) {return `:E:${document.URL}: ${e}`;}
} catch(e) {return wrapResult({result: 'error', debugInfo: [document.URL], error: e});}
})();
'''
