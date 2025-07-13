const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

module.exports = defineConfig({
  transpileDependencies: true,
  filenameHashing: false,  // 禁用文件名hash后缀
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        },
        ws: true
      },
      '/data': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/data': '/data'
        },
      }
    }
  },
  configureWebpack: {
    resolve: {
      fallback: {
        "url": false,
        "http": false,
        "https": false,
        "zlib": false,
        "stream": false,
        "util": false,
        "buffer": false,
        "crypto": false,
        "process": false,
        "assert": false
      }
    },
    plugins: [
      new webpack.ProvidePlugin({
        process: 'process/browser',
      })
    ]
  }
})
