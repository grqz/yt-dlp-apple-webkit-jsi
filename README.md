A yt-dlp-plugin that uses Apple WebKit to solve Youtube N/Sig, should work on most modern apple devices.


# Installing

## Requirements
<!--TODO: 3.10+-->
1. Python. CPython 3.9+ and PyPy 3.10+ are supported. Other implementations and versions might or might not work.
2. A device with Apple's operating system. This plugin _should_ work on iOS 14.0+, and MacOS 12.0+, on x86\_64 or arm64. Other apple's operating systems might or might not work.
3. yt-dlp **`2025.<TODO:MinVer>`** or above. Requires [yt-dlp/yt-dlp#14157](<https://github.com/yt-dlp/yt-dlp/pull/14157>)

## Installing the plugin

**pip/pipx**

If yt-dlp is installed through `pip` or `pipx`, you can install the plugin with the following:

```
pipx inject yt-dlp yt-dlp-apple-webkit-jsi
```
or

```
python3 -m pip install -U yt-dlp-apple-webkit-jsi
```

**Manual**

1. Go to the [latest release](<https://github.com/grqz/yt-dlp-apple-webkit-jsi/releases/latest>)
2. Find `yt-dlp-apple-webkit-jsi.zip` and download it to one of the [yt-dlp plugin locations](<https://github.com/yt-dlp/yt-dlp#installing-plugins>)

    - User Plugins
        - `${XDG_CONFIG_HOME}/yt-dlp/plugins`
        - `~/.yt-dlp/plugins/`
    
    - System Plugins
       -  `/etc/yt-dlp/plugins/`
       -  `/etc/yt-dlp-plugins/`
    
    - Executable location
        - Binary: where `<root-dir>/yt-dlp`, `<root-dir>/yt-dlp-plugins/`

For more locations and methods, see [installing yt-dlp plugins](<https://github.com/yt-dlp/yt-dlp#installing-plugins>)

---

If installed correctly, you should see the provider's version in `yt-dlp -v` output:

    [debug] [youtube] [jsc] JS Challenge Providers: bun (unavailable), deno (unavailable), jsinterp (unavailable), node (unavailable), apple-webkit-jsi-0.0.1 (external)
