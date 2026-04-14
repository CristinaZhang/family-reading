const { request } = require("../../utils/api");

Page({
  data: {
    reading: null,
    loading: true,
    error: false,
    progress: 0,
    readingId: null,
    familyId: null,
  },

  onLoad(options) {
    const { id } = options;
    this.setData({ readingId: id });
    this.getReadingDetail(id);
  },

  async getReadingDetail(id) {
    try {
      this.setData({ loading: true, error: false });

      // 调用API获取阅读记录详情
      const reading = await request("GET", `/v1/readings/${id}`);
      const book = reading.book || {};

      // 获取家庭信息
      const families = await request("GET", "/v1/families");
      if (families && families.length > 0) {
        this.setData({ familyId: families[0].id });
      }

      this.setData({
        reading: {
          id: reading.id,
          book: {
            title: book.title || "未知书籍",
            author: (book.authors || []).join(", ") || "未知作者",
            cover: book.cover_url || null,
            isbn: book.isbn13 || "",
            pages: null,
          },
          status: reading.status,
          progress: reading.progress_value,
          startDate: reading.started_on || "未知",
          updatedAt: reading.updated_at,
          note: reading.note || "",
        },
        progress: reading.progress_value,
        loading: false,
      });
    } catch (e) {
      console.error('获取阅读详情失败:', e);
      this.setData({ error: true, loading: false });
      wx.showToast({
        title: '获取阅读详情失败',
        icon: 'none',
      });
    }
  },

  updateProgress(e) {
    const progress = e.detail.value;
    this.setData({ progress });
  },

  async saveProgress() {
    try {
      const readingId = this.data.readingId;
      if (!readingId) {
        wx.showToast({ title: '阅读记录不存在', icon: 'none' });
        return;
      }

      wx.showLoading({ title: '保存中...' });

      await request("PATCH", `/v1/readings/${readingId}`, {
        progress_value: this.data.progress,
      });

      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
    } catch (e) {
      console.error('保存进度失败:', e);
      wx.hideLoading();
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
    }
  },

  refresh() {
    const { reading } = this.data;
    if (reading) {
      this.getReadingDetail(reading.id);
    }
  },
});
