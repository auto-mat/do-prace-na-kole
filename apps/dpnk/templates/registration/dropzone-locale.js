//https://stackoverflow.com/a/38732545/2126889
{% load i18n %}
Dropzone.prototype.defaultOptions.dictDefaultMessage = "{% trans 'Drop files here to upload' %}";
Dropzone.prototype.defaultOptions.dictFallbackMessage = "{% trans 'Your browser does not support drag&drop file uploads.' %}";
Dropzone.prototype.defaultOptions.dictFallbackText = "{% trans 'Please use the fallback form below to upload your files like in the olden days.' %}";
Dropzone.prototype.defaultOptions.dictFileTooBig = "{% trans 'File is too big ({{filesize}}MiB). Max filesize: {{maxFilesize}}MiB.' %}";
Dropzone.prototype.defaultOptions.dictInvalidFileType = "{% trans 'Only valid GPX files are supported.' %}";
Dropzone.prototype.defaultOptions.dictResponseError = "{% trans 'Server responded with {{statusCode}} code.' %}";
