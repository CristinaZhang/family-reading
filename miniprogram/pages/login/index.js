const { request } = require("../../utils/api");

Page({
  data: {
    openid: "dev-user-1",
  },

  onInput(e) {
    this.setData({ openid: e.detail.value });
  },

  async login() {
    try {
      const res = await request("POST", "/v1/auth/dev/login", { openid: this.data.openid });
      wx.setStorageSync("access_token", res.access_token);
      wx.setStorageSync("user", res.user);
      wx.showToast({ title: "登录成功" });
      wx.reLaunch({ url: "/pages/home/index" });
    } catch (e) {
      wx.showModal({
        title: "登录失败",
        content: (e && e.data && e.data.detail) || "请检查后端是否启动、BASE_URL 是否正确",
        showCancel: false,
      });
    }
  },
});

