Page({
  data: {
    isbn: ""
  },

  onLoad() {
    // 页面加载时自动调用扫码
    this.scanISBN();
  },

  scanISBN() {
    wx.scanCode({
      onlyFromCamera: true,
      success: (res) => {
        const isbn = res.result;
        this.setData({ isbn });
        this.addBookByISBN(isbn);
      },
      fail: (err) => {
        wx.showToast({
          title: '扫码失败，请重试',
          icon: 'none'
        });
      }
    });
  },

  async addBookByISBN(isbn) {
    try {
      // 这里应该调用API解析ISBN
      wx.showLoading({ title: '正在解析书籍...' });
      // 模拟API调用
      setTimeout(() => {
        wx.hideLoading();
        wx.showToast({
          title: '书籍添加成功',
          icon: 'success'
        });
        wx.navigateBack();
      }, 1000);
    } catch (e) {
      wx.hideLoading();
      wx.showToast({
        title: '添加失败，请重试',
        icon: 'none'
      });
    }
  }
});