// ============================================
// 调试模式切换（真机/模拟器）
// 'localhost' — 模拟器本地调试
// 'lan'       — 真机调试（同一局域网）
// ============================================
const MODE = 'localhost';
const LAN_IP = '192.168.0.106';

const BASE_URL = MODE === 'lan'
  ? `http://${LAN_IP}:8000`
  : 'http://127.0.0.1:8000';

console.log(`[config] MODE=${MODE} BASE_URL=${BASE_URL}`);

module.exports = {
  BASE_URL,
};
