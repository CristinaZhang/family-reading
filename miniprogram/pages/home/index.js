const { request } = require("../../utils/api");

Page({
  data: {
    family: null,
    members: [],
    dash: null,
  },

  async onShow() {
    const token = wx.getStorageSync("access_token");
    if (!token) return wx.reLaunch({ url: "/pages/login/index" });
    await this.bootstrap();
  },

  async bootstrap() {
    // MVP：后端目前只支持"我作为 owner 的家庭列表"
    const families = await request("GET", "/v1/families");
    if (!families.length) {
      const fam = await request("POST", "/v1/families", { name: "我家" });
      this.setData({ family: fam });
    } else {
      this.setData({ family: families[0] });
    }

    const members = await request("GET", `/v1/families/${this.data.family.id}/members`);
    if (!members.length) {
      // 默认创建一个"我"，方便快速体验
      await request("POST", `/v1/families/${this.data.family.id}/members`, { display_name: "我" });
    }

    await this.refresh();
  },

  async refresh() {
    const members = await request("GET", `/v1/families/${this.data.family.id}/members`);
    const dash = await request("GET", `/v1/families/${this.data.family.id}/dashboard`);
    this.setData({ members, dash });
  },

  goSettings() {
    wx.navigateTo({ url: "/pages/settings/index" });
  },

  logout() {
    wx.removeStorageSync("access_token");
    wx.removeStorageSync("user");
    wx.reLaunch({ url: "/pages/login/index" });
  },
});
