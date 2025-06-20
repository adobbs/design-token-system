const StyleDictionary = require('style-dictionary');

module.exports = {
  source: [
    "tokens/tokens.json"
  ],
  platforms: {
    web: {
      transformGroup: 'web',
      buildPath: 'dist/web/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables',
        selector: ':root'
      }, {
        destination: 'tokens.json',
        format: 'json/flat'
      }, {
        destination: 'tokens-nested.json',
        format: 'json/nested'
      }]
    },
    scss: {
      transformGroup: 'scss',
      buildPath: 'dist/scss/',
      files: [{
        destination: 'tokens.scss',
        format: 'scss/variables'
      }]
    },
    ios: {
      transformGroup: 'ios',
      buildPath: 'dist/ios/',
      files: [{
        destination: 'DesignTokens.swift',
        format: 'ios-swift/class.swift',
        className: 'DesignTokens'
      }, {
        destination: 'DesignTokens.h',
        format: 'ios/macros'
      }]
    },
    android: {
      transformGroup: 'android',
      buildPath: 'dist/android/',
      files: [{
        destination: 'design_tokens.xml',
        format: 'android/resources'
      }, {
        destination: 'DesignTokens.java',
        format: 'android/colors',
        className: 'DesignTokens'
      }]
    },
    flutter: {
      transformGroup: 'flutter',
      buildPath: 'dist/flutter/',
      files: [{
        destination: 'design_tokens.dart',
        format: 'flutter/class.dart',
        className: 'DesignTokens'
      }]
    },
    json: {
      transformGroup: 'web',
      buildPath: 'dist/json/',
      files: [{
        destination: 'tokens-flat.json',
        format: 'json/flat'
      }, {
        destination: 'tokens-nested.json',
        format: 'json/nested'
      }]
    }
  }
};