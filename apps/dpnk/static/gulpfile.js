var gulp = require('gulp');
var ts = require('gulp-typescript');
var watchify = require('watchify');
var fancy_log = require('fancy-log');
var browserify = require('browserify');
var source = require('vinyl-source-stream');
var tsify = require('tsify');

var tsProject = ts.createProject('tsconfig.json');

var watchedBrowserify = watchify(browserify({
    basedir: '.',
    debug: true,
    entries: [
        'ts/form_functions.ts'
    ],
    cache: {},
    packageCache: {}
}).plugin(tsify));

function bundle() {
    return watchedBrowserify
        .bundle()
        .on('error', fancy_log)
        .pipe(source('bundle.js'))
        .pipe(gulp.dest('js'));
}

gulp.task('default', bundle);

watchedBrowserify.on('update', bundle);
watchedBrowserify.on('log', fancy_log);
