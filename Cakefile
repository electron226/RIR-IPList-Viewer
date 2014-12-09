exec = (require 'child_process').exec

FILES_COFFEE = [
    'js/index.coffee',
    'js/custom.coffee'
]
FILES_LESS = [
    'css/style.less',
    'css/custom.less'
]

FilePathNoEXT = (filename) ->
    return filename.substr(0, filename.lastIndexOf("."))

compileLess = (file) ->
    exec "lessc #{file} #{file.replace('.less', '.css')}", (err, stdout, stderr) ->
        return console.error err if err
        console.log "Compiled #{file}"

reduceLess = (file) ->
    NOEXT_CSS = FilePathNoEXT(file)
    exec "yui-compressor --type css --charset UTF-8 -o #{NOEXT_CSS}.min.css #{NOEXT_CSS}.css", (err, stdout, stderr) ->
        return console.error err if err
        console.log "minimized from #{NOEXT_CSS}.css to #{NOEXT_CSS}.min.css"

compileCoffee = (file) ->
    exec "coffee -c #{file}", (err, stdout, stderr) ->
        return console.error err if err
        console.log "Compiled #{file}"

reduceCoffee = (file) ->
    NOEXT_JS = FilePathNoEXT(file)
    exec "compiler --js_output_file #{NOEXT_JS}.min.js --js #{NOEXT_JS}.js", (err, stdout, stderr) ->
        return console.error err if err
        console.log "minimized from #{NOEXT_JS}.js to #{NOEXT_JS}.min.js"

task 'build', 'compile less and coffee script.', (options) ->
    compileLess(file) for file in FILES_LESS
    compileCoffee(file) for file in FILES_COFFEE

task 'reduce', 'reduce less and coffee script.', (options) ->
    reduceLess(file) for file in FILES_LESS
    reduceCoffee(file) for file in FILES_COFFEE
