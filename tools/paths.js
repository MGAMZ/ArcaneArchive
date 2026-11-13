// 采集工作目录与浏览器配置目录。
const os = require('os');
const path = require('path');

const WORK = process.env.SKLAND_WORK || path.join(__dirname, '..', 'work', 'skland');
// 浏览器配置要放在原生盘上，9p 挂载的仓内建不了它要的链接。
const PROFILE = process.env.SKLAND_PROFILE ||
  path.join(os.homedir(), '.cache', 'arcane-archive', 'profile');

module.exports = { WORK, PROFILE };