const { request } = require("../../utils/api");

Page({
  data: {
    family: null,
    members: [],
    loading: true,
    error: false,
    editingFamilyName: false,
    familyName: "",
    newMemberName: "",
    showAddMember: false,
  },

  async onShow() {
    const token = wx.getStorageSync("access_token");
    if (!token) return wx.reLaunch({ url: "/pages/login/index" });
    await this.loadFamily();
  },

  async loadFamily() {
    try {
      this.setData({ loading: true, error: false });

      const families = await request("GET", "/v1/families");
      if (!families.length) {
        const fam = await request("POST", "/v1/families", { name: "我家" });
        this.setData({ family: fam, familyName: fam.name });
      } else {
        this.setData({ family: families[0], familyName: families[0].name });
      }

      await this.loadMembers();
    } catch (e) {
      console.error('加载家庭信息失败:', e);
      this.setData({ error: true, loading: false });
    }
  },

  async loadMembers() {
    try {
      const familyId = this.data.family.id;
      const members = await request("GET", `/v1/families/${familyId}/members`);
      this.setData({ members, loading: false });
    } catch (e) {
      console.error('加载成员失败:', e);
      this.setData({ loading: false });
    }
  },

  onFamilyNameInput(e) {
    this.setData({ familyName: e.detail.value });
  },

  async saveFamilyName() {
    const name = this.data.familyName.trim();
    if (!name) {
      wx.showToast({ title: '名称不能为空', icon: 'none' });
      return;
    }

    // 后端暂无修改家庭名的接口，提示用户
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },

  onMemberNameInput(e) {
    this.setData({ newMemberName: e.detail.value });
  },

  showAddMemberInput() {
    this.setData({ showAddMember: true });
  },

  hideAddMemberInput() {
    this.setData({ showAddMember: false, newMemberName: "" });
  },

  async addMember() {
    const name = this.data.newMemberName.trim();
    if (!name) {
      wx.showToast({ title: '请输入成员名称', icon: 'none' });
      return;
    }

    try {
      const familyId = this.data.family.id;
      const member = await request("POST", `/v1/families/${familyId}/members`, {
        display_name: name,
      });

      this.setData({
        members: [...this.data.members, member],
        showAddMember: false,
        newMemberName: "",
      });

      wx.showToast({ title: '添加成功', icon: 'success' });
    } catch (e) {
      console.error('添加成员失败:', e);
      wx.showToast({ title: '添加失败，请重试', icon: 'none' });
    }
  },

  goBack() {
    wx.navigateBack();
  },
});
