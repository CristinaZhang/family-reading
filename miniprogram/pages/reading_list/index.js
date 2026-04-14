const { request } = require("../../utils/api");

Page({
  data: {
    readingList: [],
    loading: true,
    error: false,
    familyId: null
  },

  async onLoad() {
    const token = wx.getStorageSync("access_token");
    if (!token) return wx.reLaunch({ url: "/pages/login/index" });
    await this.bootstrap();
  },

  async bootstrap() {
    try {
      // 获取家庭列表
      const families = await request("GET", "/v1/families");
      if (!families.length) {
        // 如果没有家庭，创建一个
        const fam = await request("POST", "/v1/families", { name: "我家" });
        this.setData({ familyId: fam.id });
      } else {
        // 使用第一个家庭
        this.setData({ familyId: families[0].id });
      }

      // 获取阅读记录列表
      await this.getReadingList();
    } catch (e) {
      console.error('初始化失败:', e);
      this.setData({ error: true, loading: false });
      wx.showToast({
        title: '初始化失败',
        icon: 'none'
      });
    }
  },

  async getReadingList() {
    try {
      this.setData({ loading: true, error: false });

      // 调用API获取阅读记录列表
      const familyId = this.data.familyId;
      if (!familyId) {
        throw new Error('家庭ID不存在');
      }

      const readings = await request("GET", `/v1/families/${familyId}/readings`);
      console.log('阅读记录:', readings);

      // 转换阅读记录格式
      const readingList = readings.map(reading => {
        const book = reading.book || {};
        return {
          id: reading.id,
          book: {
            title: book.title || "未知书籍",
            author: (book.authors || []).join(", ") || "未知作者",
            cover: book.cover_url || null
          },
          status: reading.status,
          progress: reading.progress_value,
          updatedAt: reading.updated_at
        };
      });

      this.setData({ readingList, loading: false });
    } catch (e) {
      console.error('获取阅读记录失败:', e);
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