
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "http",
                    host: "191.96.104.44",
                    port: parseInt(5781)
                },
                bypassList: ["localhost"]
            }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        chrome.webRequest.onAuthRequired.addListener(
            function(details) {
                return {
                    authCredentials: {
                        username: "mkbiyugv",
                        password: "mnq25ygajv12"
                    }
                };
            },
            {urls: ["<all_urls>"]},
            ["blocking"]
        );
        