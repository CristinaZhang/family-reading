/**
 * WeChat miniprogram wx API mock
 * All wx.* globals used across the codebase are mocked here.
 * Loaded once via setupFilesAfterEnv — DO NOT re-require this module in tests.
 */

const wx = {
  // Storage
  getStorageSync: jest.fn(() => null),
  setStorageSync: jest.fn(),
  removeStorageSync: jest.fn(),

  // Network
  request: jest.fn(),

  // Navigation
  navigateTo: jest.fn(({ url }) => Promise.resolve({ url })),
  navigateBack: jest.fn(),
  reLaunch: jest.fn(({ url }) => Promise.resolve({ url })),

  // UI feedback
  showToast: jest.fn(({ title }) => Promise.resolve({ title })),
  showModal: jest.fn(({ title, content, showCancel }) => {
    return Promise.resolve({ confirm: true, cancel: false });
  }),
  showLoading: jest.fn(({ title }) => Promise.resolve({ title })),
  hideLoading: jest.fn(),
  stopPullDownRefresh: jest.fn(),

  // Login
  login: jest.fn(({ success }) => {
    success({ code: 'test-wechat-code' });
  }),
};

global.wx = wx;

module.exports = wx;
