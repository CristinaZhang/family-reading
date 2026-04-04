const { request } = require("../../utils/api");

Page({
  data: {
    reading: null,
    loading: true,
    error: false,
    progress: 0
  },

  onLoad(options) {
    const { id } = options;
    this.getReadingDetail(id);
  },

  async getReadingDetail(id) {
    try {
      this.setData({ loading: true, error: false });
      // 这里应该调用API获取阅读记录详情
      // 模拟API调用
      setTimeout(() => {
        const mockData = {
          id: id,
          book: {
            title: "小王子",
            author: "安托万·德·圣-埃克苏佩里",
            cover: "https://example.com/cover1.jpg",
            isbn: "9787544270878",
            pages: 200
          },
          status: "reading",
          progress: 50,
          startDate: "2024-01-01",
          updatedAt: "2024-01-05",
          note: "这是一本非常经典的童话书，值得一读。"
        };
        this.setData({
          reading: mockData,
          progress: mockData.progress,
          loading: false
        });
      }, 1000);
    } catch (e) {
      this.setData({ error: true, loading: false });
      wx.showToast({
        title: '获取阅读详情失败',
        icon: 'none'
      });
    }
  },

  updateProgress(e) {
    const progress = e.detail.value;
    this.setData({ progress });
  },

  async saveProgress() {
    try {
      wx.showLoading({ title: '保存中...' });
      // 这里应该调用API更新阅读进度
      // 模拟API调用
      setTimeout(() => {
        wx.hideLoading();
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
      }, 1000);
    } catch (e) {
      wx.hideLoading();
      wx.showToast({
        title: '保存失败，请重试',
        icon: 'none'
      });
    }
  },

  refresh() {
    const { reading } = this.data;
    if (reading) {
      this.getReadingDetail(reading.id);
    }
  }
});