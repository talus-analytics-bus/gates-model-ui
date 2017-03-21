var gulp = require('gulp'),
		concat = require('gulp-concat'),
		uglify = require('gulp-uglify'),
		rename = require('gulp-rename'),
		babel = require('gulp-babel'),
		eslint = require('gulp-eslint');

gulp.task('default', ['build-js']);

gulp.task('lint', function() {
	return gulp.src(['./js/**/*.js', '!node_modules/**'])
		.pipe(eslint())
		.pipe(eslint.format());
});

gulp.task('build-js', function() {
	return gulp.src([
		'./js/utility.js',
		'./js/routing.js',
		'./js/app.js',
		'./js/**/*.js',
		'./js/*.js',
	])
		.pipe(concat('bundle.js'))
		.pipe(babel({ presets: ['es2015'] }))
		.pipe(uglify())
		.pipe(rename({ suffix: '.min' }))
		.pipe(gulp.dest('build'));
});

gulp.task('build-css', function() {
	return gulp.src([
		'./css/bootstrap.min.css',
		'./css/!(main)*.css',
		'./css/main.css',
	])
		.pipe(concat('bundle.css'))
		.pipe(gulp.dest('build'));
});

gulp.task('build-lib', function() {
	return gulp.src([
		'lib/jquery-2.2.0.min.js',
		'lib/signals.min.js',
		'lib/*.js',
	])
		.pipe(concat('lib.js'))
		.pipe(uglify())
		.pipe(rename({ suffix: '.min' }))
		.pipe(gulp.dest('build'));
});
