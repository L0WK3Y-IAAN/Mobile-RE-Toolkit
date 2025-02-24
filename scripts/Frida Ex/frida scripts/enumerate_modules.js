console.log("Loaded Modules:");
Process.enumerateModules().forEach(function(module) {
    console.log(module.name);
});
