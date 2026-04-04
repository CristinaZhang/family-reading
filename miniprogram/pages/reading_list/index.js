const { request } = require("../../utils/api");

Page({
  data: {
    readingList: [],
    loading: true,
    error: false
  },

  onLoad() {
    this.getReadingList();
  },

  async getReadingList() {
    try {
      this.setData({ loading: true, error: false });
      // 这里应该调用API获取阅读记录列表
      // 模拟API调用
      setTimeout(() => {
        const mockData = [
          {
            id: 1,
            book: {
              title: "小王子",
              author: "安托万·德·圣-埃克苏佩里",
              cover: "https://example.com/cover1.jpg"
            },
            status: "reading",
            progress: 50,
            updatedAt: "2024-01-01"
          },
          {
            id: 2,
            book: {
              title: "哈利·波特",
              author: "J.K.罗琳",
              cover: "https://example.com/cover2.jpg"
            },
            status: "finished",
            progress: 100,
            updatedAt: "2024-01-02"
          }
        ];
        this.setData({ readingList: mockData, loading: false });
      }, 1000);
    } catch (e) {
      this.setData({ error: true, loading: false });
      wx.showToast({
        title: '获取阅读记录失败',
        icon: 'none'
      });
    }
  },

  goToDetail(e) {
    const readingId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/reading_detail/index?id=${readingId}`
    });
  },

  refresh() {
    this.getReadingList();
  }
});