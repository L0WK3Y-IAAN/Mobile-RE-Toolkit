Java.perform(function () {
  var callTree = {}; // Stores function call tree
  var currentDepth = 0; // Tracks depth of function calls

  function logCall(functionName) {
      if (!callTree[currentDepth]) callTree[currentDepth] = [];
      callTree[currentDepth].push(functionName);
  }

  function printExecutionTree(tree, depth) {
      if (!tree[depth]) return;
      tree[depth].forEach(function (func) {
          console.log("  ".repeat(depth) + "↳ " + func);
          printExecutionTree(tree, depth + 1);
      });
  }

  console.log("[+] Hooking Button Clicks and Linking Calls...");

  var Button = Java.use("android.widget.Button");
  var ViewOnClickListener = Java.use("android.view.View$OnClickListener");

  Button.setOnClickListener.implementation = function (listener) {
      console.log("[+] Hooked: setOnClickListener() called");

      if (listener === null) {
          console.log("[!] No listener was set, skipping hook.");
          return this.setOnClickListener(listener);
      }

      var retainedListener = Java.retain(listener);

      var WrappedClickListener = Java.registerClass({
          name: "com.example.HookedClickListener",
          implements: [ViewOnClickListener],
          fields: {
              originalListener: "android.view.View$OnClickListener"
          },
          methods: {
              onClick: function (view) {
                  console.log("\n[+] Button Clicked! Building execution tree...");
                  callTree = {}; // Reset tree on each button click
                  currentDepth = 0;

                  traceKeyJavaMethods();
                  hookNativeFunctions();

                  if (this.originalListener.value !== null) {
                      console.log("[+] Calling original listener...");
                      this.originalListener.value.onClick(view);
                  } else {
                      console.log("[!] Original listener is null.");
                  }

                  // Print execution tree
                  console.log("\n[+] Execution Tree:");
                  printExecutionTree(callTree, 0);
              }
          }
      });

      var wrappedInstance = WrappedClickListener.$new();
      wrappedInstance.originalListener.value = retainedListener;

      this.setOnClickListener(wrappedInstance);
  };

  function traceKeyJavaMethods() {
      var Activity = Java.use("android.app.Activity");

      // Handle overloaded onCreate methods
      Activity.onCreate.overload('android.os.Bundle').implementation = function (bundle) {
          logCall("Activity.onCreate(Bundle)");
          return this.onCreate(bundle);
      };

      Activity.onCreate.overload('android.os.Bundle', 'android.os.PersistableBundle').implementation = function (bundle, persistableBundle) {
          logCall("Activity.onCreate(Bundle, PersistableBundle)");
          return this.onCreate(bundle, persistableBundle);
      };

      var Intent = Java.use("android.content.Intent");
      Intent.setAction.implementation = function (action) {
          logCall("Intent.setAction: " + action);
          return this.setAction(action);
      };

      var PackageManager = Java.use("android.content.pm.PackageManager");
      PackageManager.getApplicationInfo.implementation = function (name, flag) {
          logCall("PackageManager.getApplicationInfo: " + name);
          return this.getApplicationInfo(name, flag);
      };

      var URL = Java.use("java.net.URL");

      // Fix: Handle overloaded openConnection methods explicitly
      URL.openConnection.overload().implementation = function () {
          logCall("URL.openConnection()");
          return this.openConnection();
      };

      URL.openConnection.overload('java.net.Proxy').implementation = function (proxy) {
          logCall("URL.openConnection(Proxy)");
          return this.openConnection(proxy);
      };
  }

  function hookNativeFunctions() {
      var libdl = Module.findExportByName(null, "dlopen");
      var dlsym = Module.findExportByName(null, "dlsym");

      if (libdl) {
          Interceptor.attach(libdl, {
              onEnter: function (args) {
                  var libname = Memory.readUtf8String(args[0]);
                  logCall("dlopen: " + libname);
              }
          });
      }

      if (dlsym) {
          Interceptor.attach(dlsym, {
              onEnter: function (args) {
                  var symbol = Memory.readUtf8String(args[1]);
                  logCall("dlsym: " + symbol);
              }
          });
      }
  }
});
