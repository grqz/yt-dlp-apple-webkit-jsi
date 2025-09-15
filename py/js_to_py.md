# Mappings between Javascript and Python objects (through the WebKit API)

## Javascript return values

Example code (RuntimeError will be thrown if you return an unsupported object):

```js
let x = {};
return Object.defineProperty(x, 'computed', {
    get() { return this._value * 2; },
    set(v) { this._value = v / 2; },
    enumerable: true
}),  // will appear as 60.0
// x.fn = () => {},  // functions are unsupported
x._value = 30,  // will be a float
x._self_ = x,  // this will be another object, whose _self_ points to itself
x.dt = new Date,  // dt.datetime in utc
x.u8arr = new Uint8Array([3, 46, 7]),
x.carr = [[7, undefined],[3,7],[4,2],[8,0]],
x.carr[0][1] = x.carr,
x.map = new Map(x.carr),  // same as _self_
x.mapNoCirc = new Map([[3,7],[4,2],[8,0]]),
x.nan = NaN,  // math.nan
x.inf = Infinity,  // math.inf
x.ninf = -Infinity,  // -math.inf
x.nzr = -0,  // -0.0
x._bstr = 'a\u0000\n\tbあx',  // unicode is supported, and the string does not get truncated at '\0'
x.bint = 123456789012345678901234567890n,  // same as undefined
//x.sym = Symbol('I'),  // unsupported
//x.si = Symbol.iterator,  // unsupported
x.ab = new ArrayBuffer(8),  // {}
x.set = new Set([3, 5, 2]),  // {}
x.re = /\s*\d+\s*/gi,  // {}
x['ああ'] = null,  // <null object>
x['あ'] = undefined,  // discarded in dictionaries/undefined if at top level/undefined in arrays
//x.wm = new WeakMap,  // unsupported
//x.ws = new WeakSet,  // unsupported
//x.td = new TextDecoder,  // unsupported
x.__proto__ = {in: 32},  // discarded
x.booleanv = [true, false],  // coerced to [1, 0]
x.arrBint = [123456789012345678901234567890n, undefined],  // [<null object>, <null object>]
x.arrWithBlank = new Array(5),
x.arrWithBlank[0] = 'first',
x.arrWithBlank[4] = 'last',
//x.args = [arguments],  // unsupported
//x.clsm = Map,  // unsupported
x.instWMeth = {y: 6, __proto__: {x: 3, foo() {return this.y}}},
x.realfloat = 0.1 + 0.2,  // obviously not 0.3
//x.prom = Promise.resolve(42),  // unsupported
//x.canvas = document.createElement('canvas'), // unsupported
//x.xhr = new XMLHttpRequest,  // unsupported
x;
```

The return value you will get from python(pprinted, undefined=None, null=_NullTag):
```log
{'_bstr': 'a\x00\n\tbあx',
 '_self_': {'_bstr': 'a\x00\n\tbあx',
            '_self_': <Recursion on dict with id=4351871744>,
            '_value': 30.0,
            'ab': {},
            'arrBint': [<class '__main__._NullTag'>,
                        <class '__main__._NullTag'>],
            'arrWithBlank': ['first',
                             <class '__main__._NullTag'>,
                             <class '__main__._NullTag'>,
                             <class '__main__._NullTag'>,
                             'last'],
            'booleanv': [1, 0],
            'carr': [[7.0,
                      [<Recursion on list with id=4351262592>,
                       [3.0, 7.0],
                       [4.0, 2.0],
                       [8.0, 0.0]]],
                     [3.0, 7.0],
                     [4.0, 2.0],
                     [8.0, 0.0]],
            'computed': 60.0,
            'dt': datetime.datetime(2025, 9, 15, 0, 12, 2, 494000, tzinfo=datetime.timezone.utc),
            'inf': inf,
            'instWMeth': {'y': 6.0},
            'map': {},
            'mapNoCirc': {},
            'nan': nan,
            'ninf': -inf,
            'nzr': -0.0,
            're': {},
            'realfloat': 0.30000000000000004,
            'set': {},
            'u8arr': {'0': 3.0, '1': 46.0, '2': 7.0},
            'ああ': <class '__main__._NullTag'>},
 '_value': 30.0,
 'ab': {},
 'arrBint': [<class '__main__._NullTag'>, <class '__main__._NullTag'>],
 'arrWithBlank': ['first',
                  <class '__main__._NullTag'>,
                  <class '__main__._NullTag'>,
                  <class '__main__._NullTag'>,
                  'last'],
 'booleanv': [1, 0],
 'carr': [[7.0, <Recursion on list with id=4348490752>],
          [3.0, 7.0],
          [4.0, 2.0],
          [8.0, 0.0]],
 'computed': 60.0,
 'dt': datetime.datetime(2025, 9, 15, 0, 12, 2, 494000, tzinfo=datetime.timezone.utc),
 'inf': inf,
 'instWMeth': {'y': 6.0},
 'map': {},
 'mapNoCirc': {},
 'nan': nan,
 'ninf': -inf,
 'nzr': -0.0,
 're': {},
 'realfloat': 0.30000000000000004,
 'set': {},
 'u8arr': {'0': 3.0, '1': 46.0, '2': 7.0},
 'ああ': <class '__main__._NullTag'>}
```
