var gulp = require('gulp'),
	concat = require('gulp-concat'),
	uglify = require('gulp-uglify'),
	rename = require('gulp-rename');
		
gulp.task('default', ['minify-js', 'minify-css']);

gulp.task('minify-js', function() {
	gulp.src([
		'./js/!(app)*.js',
		'./js/pages/*.js',
		'./js/app.js'
	])
		.pipe(concat('bundle.js'))
		.pipe(uglify())
		.pipe(rename({suffix: '.min'}))
		.pipe(gulp.dest('build'));
});

gulp.task('minify-css', function() {
	gulp.src([
		'./css/bootstrap.min.css',
		'./css/!(main)*.css',
		'./css/main.css'
	])
		.pipe(concat('bundle.css'))
		.pipe(gulp.dest('build'));
});

gulp.task('minify-lib', function() {
	gulp.src([
		'lib/jquery-2.2.0.min.js',
		'lib/signals.min.js',
		'lib/*.js'
	])	
		.pipe(concat('lib.js'))
		.pipe(uglify())
		.pipe(rename({suffix: '.min'}))
		.pipe(gulp.dest('build'));
});
