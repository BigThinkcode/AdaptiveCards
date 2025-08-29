module.exports = (api) => {
    api.cache(true)
  
    return {
        presets: ['module:@react-native/babel-preset'],
    }
}