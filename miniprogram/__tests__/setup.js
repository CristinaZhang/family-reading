// Test setup — loads wx mocks and registers global helpers
require('../__mocks__/wx');

// Simulate Page() and App() so page JS files can be required without error
global.Page = jest.fn((config) => config);
global.App = jest.fn((config) => config);
global.getApp = jest.fn(() => global.Page);

// Clear mock call history before each test
// Use mockClear (not clearAllMocks) to preserve implementations set by tests
beforeEach(() => {
  const wxKeys = ['getStorageSync', 'setStorageSync', 'removeStorageSync', 'request',
    'navigateTo', 'navigateBack', 'reLaunch', 'showToast', 'showModal',
    'showLoading', 'hideLoading', 'stopPullDownRefresh', 'login'];
  wxKeys.forEach((key) => {
    if (global.wx[key] && global.wx[key].mockClear) {
      global.wx[key].mockClear();
    }
  });
  global.Page.mockClear();
});
