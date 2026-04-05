const { request } = require("../../utils/api");

Page({
  data: {
    loading: false,
  },

  async onLoad() {
    // 页面加载时检查是否已登录
    const token = wx.getStorageSync("access_token");
    if (token) {
      wx.reLaunch({ url: "/pages/home/index" });
    }
  },

  async login() {
    try {
      this.setData({ loading: true });
      console.log('=== 开始微信登录流程 ===');

      // 调用微信登录API获取code
      wx.login({
        success: async (res) => {
          console.log('微信登录API调用成功:', res);
          if (res.code) {
            console.log('获取到微信登录code:', res.code);
            try {
              console.log('调用后端微信登录接口...');
              // 调用后端微信登录接口
              const loginRes = await request("POST", "/v1/auth/wechat/login", { code: res.code });
              console.log('后端登录接口返回:', loginRes);

              wx.setStorageSync("access_token", loginRes.access_token);
              wx.setStorageSync("user", loginRes.user);
              console.log('登录成功，保存token:', loginRes.access_token);

              wx.showToast({ title: "登录成功" });
              console.log('跳转到首页...');
              wx.reLaunch({ url: "/pages/home/index" });
            } catch (e) {
              console.error('后端登录接口调用失败:', e);
              wx.showModal({
                title: "登录失败",
                content: (e && e.data && e.data.detail) || "微信登录失败，请重试",
                showCancel: false,
              });
            } finally {
              this.setData({ loading: false });
              console.log('登录流程结束');
            }
          } else {
            console.error('获取微信登录凭证失败:', res);
            wx.showModal({
              title: "登录失败",
              content: "获取微信登录凭证失败，请重试",
              showCancel: false,
            });
            this.setData({ loading: false });
            console.log('登录流程结束');
          }
        },
        fail: (err) => {
          console.error('微信登录API调用失败:', err);
          wx.showModal({
            title: "登录失败",
            content: "微信登录失败，请重试",
            showCancel: false,
          });
          this.setData({ loading: false });
          console.log('登录流程结束');
        }
      });
    } catch (e) {
      console.error('登录流程异常:', e);
      wx.showModal({
        title: "登录失败",
        content: (e && e.data && e.data.detail) || "请检查后端是否启动、BASE_URL 是否正确",
        showCancel: false,
      });
      this.setData({ loading: false });
      console.log('登录流程结束');
    }
  },

  // 开发测试登录（备用）
  async devLogin() {
    try {
      this.setData({ loading: true });
      const res = await request("POST", "/v1/auth/dev/login", { openid: "dev-user-1" });
      wx.setStorageSync("access_token", res.access_token);
      wx.setStorageSync("user", res.user);
      wx.showToast({ title: "开发测试登录成功" });
      wx.reLaunch({ url: "/pages/home/index" });
    } catch (e) {
      wx.showModal({
        title: "登录失败",
        content: (e && e.data && e.data.detail) || "请检查后端是否启动、BASE_URL 是否正确",
        showCancel: false,
      });
    } finally {
      this.setData({ loading: false });
    }
  },
});