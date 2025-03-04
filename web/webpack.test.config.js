/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2022, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

/* eslint-env node */
const path = require('path');
const webpack = require('webpack');
const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');

const sourcesDir = path.resolve(__dirname, 'pgadmin/static');
const nodeModulesDir = path.resolve(__dirname, 'node_modules');
const regressionDir = path.resolve(__dirname, 'regression');

module.exports = {
  mode: 'development',
  devtool: 'inline-source-map',
  plugins: [
    new webpack.ProvidePlugin({
      jQuery: 'jquery',
      _: 'underscore',
      'window.jQuery': 'jquery',
      'moment': 'moment',
      'window.moment':'moment',
      process: 'process/browser',
      Buffer: ['buffer', 'Buffer'],
    }),
    new ImageMinimizerPlugin({
      test: /\.(jpe?g|png|gif)$/i,
      minimizerOptions: {
        // Lossless optimization with custom option
        // Feel free to experiment with options for better result for you
        plugins: [
          ['mozjpeg', { progressive: true }],
          ['optipng', { optimizationLevel: 7 }],
          ['pngquant', {quality: [0.75, .9], speed: 3}],
        ],
      },
    }),
  ],

  module: {
    rules: [{
      test: /\.jsx?$/,
      exclude: [/node_modules/, /vendor/],
      use: {
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env', {'modules': 'commonjs', 'useBuiltIns': 'usage', 'corejs': 3}], '@babel/preset-react'],
          plugins: ['@babel/plugin-proposal-class-properties'],
          sourceMap: 'inline',
        },
      },
    }, {
      test: /\.tsx?$|\.ts?$/,
      exclude: [/node_modules/, /vendor/],
      use: {
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env', {'modules': 'commonjs', 'useBuiltIns': 'usage', 'corejs': 3}], '@babel/preset-react', '@babel/preset-typescript'],
          plugins: ['@babel/plugin-proposal-class-properties', '@babel/proposal-object-rest-spread'],
          sourceMap: 'inline',
        },
      },
    }, {
      test: /\.css$/,
      type: 'asset/source',
      use: ['style-loader'],
    }, {
      test: /\.svg$/,
      oneOf: [
        {
          issuer: /\.[jt]sx?$/,
          resourceQuery: /svgr/,
          use: ['@svgr/webpack'],
        },
        {
          type: 'asset',
          parser: {
            dataUrlCondition: {
              maxSize: 4 * 1024, // 4kb
            }
          }
        },
      ],
    }, {
      test: /\.(jpe?g|png|gif)$/i,
      type: 'asset',
      parser: {
        dataUrlCondition: {
          maxSize: 4 * 1024, // 4kb
        },
      },
      generator: {
        filename: 'img/[name].[ext]',
      },
      exclude: /vendor/,
    }, {
      test: /.*slickgrid[\\\/]+slick\.(?!core)*/,
      use:[
        {
          loader: 'imports-loader',
          options: {
            type: 'commonjs',
            imports: [
              'pure|jquery.ui',
              'pure|jquery.event.drag',
              'pure|slickgrid',
            ],
          },
        },
      ],
    }, {
      test: /.*slickgrid\.plugins[\\\/]+slick\.cellrangeselector/,
      use:[
        {
          loader: 'imports-loader',
          options: {
            type: 'commonjs',
            imports: [
              'pure|jquery.ui',
              'pure|jquery.event.drag',
              'pure|slickgrid',
            ],
          },
        }, {
          loader: 'exports-loader',
          options: {
            type: 'commonjs',
            exports: 'single|Slick.CellRangeSelector',
          },
        },
      ],
    }, {
      test: /.*slickgrid[\\\/]+slick\.core.*/,
      use:[
        {
          loader: 'imports-loader',
          options: {
            type: 'commonjs',
            imports: [
              'pure|jquery.ui',
              'pure|jquery.event.drag',
            ],
          },
        }, {
          loader: 'exports-loader',
          options: {
            type: 'commonjs',
            exports: 'single|Slick',
          },
        },
      ],
    },
    {
      test: /\.js$|\.jsx$/,
      use: {
        loader: 'istanbul-instrumenter-loader',
        options: { esModules: true },
      },
      enforce: 'post',
      exclude: /node_modules|slickgrid|plugins|bundle|generated|regression|[Tt]est.js|[Ss]pecs.js|[Ss]pec.js|\.spec\.js$/,
    },
    ],
  },

  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    alias: {
      'top': path.join(__dirname, './pgadmin'),
      'jquery': path.join(__dirname, './node_modules/jquery/dist/jquery'),
      'wcdocker': path.join(__dirname, './node_modules/webcabin-docker/Build/wcDocker'),
      'alertify': path.join(__dirname, './node_modules/alertifyjs/build/alertify'),
      'jquery.event.drag': path.join(__dirname, './node_modules/slickgrid/lib/jquery.event.drag-2.3.0'),
      'jquery.ui': path.join(__dirname, './node_modules/slickgrid/lib/jquery-ui-1.11.3'),
      'color-picker': path.join(__dirname, './node_modules/@simonwep/pickr/dist/pickr.min'),
      'bignumber': path.join(__dirname, './node_modules/bignumber.js/bignumber'),
      'bootstrap.datetimepicker': path.join(__dirname, './node_modules/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.min'),
      'bootstrap.toggle': path.join(__dirname, './node_modules/bootstrap4-toggle/js/bootstrap4-toggle.min'),
      'backbone': path.join(__dirname, './node_modules/backbone/backbone'),
      'backform': path.join(__dirname, './node_modules/backform/src/backform'),
      'backgrid': path.join(__dirname, './pgadmin/static/vendor/backgrid/backgrid'),
      'backgrid.filter': path.join(__dirname, './node_modules/backgrid-filter/backgrid-filter'),
      'react': path.join(__dirname, 'node_modules/react'),
      'react-dom': path.join(__dirname, 'node_modules/react-dom'),
      'sources': sourcesDir + '/js',
      'translations': regressionDir + '/javascript/fake_translations',
      'pgadmin.browser.messages': regressionDir + '/javascript/fake_messages',
      'pgadmin.server.supported_servers': regressionDir + '/javascript/fake_supported_servers',
      'pgadmin.browser.endpoints': regressionDir + '/javascript/fake_endpoints',
      'slickgrid': nodeModulesDir + '/slickgrid/',
      'slickgrid.plugins': nodeModulesDir + '/slickgrid/plugins/',
      'slickgrid.grid': nodeModulesDir + '/slickgrid/slick.grid',
      'moment': path.join(__dirname, './node_modules/moment/moment'),
      'jsoneditor.min': path.join(__dirname, './node_modules/jsoneditor/dist/jsoneditor.min'),
      'browser': path.resolve(__dirname, 'pgadmin/browser/static/js'),
      'pgadmin': sourcesDir + '/js/pgadmin',
      'pgadmin.sqlfoldcode': sourcesDir + '/js/codemirror/addon/fold/pgadmin-sqlfoldcode',
      'pgadmin.alertifyjs': sourcesDir + '/js/alertify.pgadmin.defaults',
      'pgadmin.backgrid': sourcesDir + '/js/backgrid.pgadmin',
      'pgadmin.backform': sourcesDir + '/js/backform.pgadmin',
      'pgadmin4-tree': path.join(__dirname, 'node_modules/pgadmin4-tree'),
      'pgbrowser': path.resolve(__dirname, 'regression/javascript/fake_browser'),
      'pgadmin.schema.dir': path.resolve(__dirname, 'pgadmin/browser/server_groups/servers/databases/schemas/static/js'),
      'pgadmin.browser.layout': path.join(__dirname, './pgadmin/browser/static/js/layout'),
      'pgadmin.browser.preferences': path.join(__dirname, './pgadmin/browser/static/js/preferences'),
      'pgadmin.browser.activity': path.join(__dirname, './pgadmin/browser/static/js/activity'),
      'pgadmin.tools.erd': path.join(__dirname, './pgadmin/tools/erd/static/js'),
      'pgadmin.tools.psql': path.join(__dirname, './pgadmin/tools/psql/static/js'),
      'pgadmin.tools.sqleditor': path.join(__dirname, './pgadmin/tools/sqleditor/static/js'),
      'pgadmin.authenticate.kerberos': path.join(__dirname, './pgadmin/authenticate/static/js/kerberos'),
      'bundled_codemirror': path.join(__dirname, './pgadmin/static/bundle/codemirror'),
      'tools': path.join(__dirname, './pgadmin/tools/'),
      'pgadmin.user_management.current_user': regressionDir + '/javascript/fake_current_user',
      'pgadmin.browser.constants': regressionDir + '/javascript/fake_constants',
    },
  },
};
