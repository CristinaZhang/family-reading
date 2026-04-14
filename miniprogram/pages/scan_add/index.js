const { request } = require("../../utils/api");

Page({
  data: {
    title: "",
    authors: "",
    publisher: "",
    loading: false,
    // 批量输入书籍名字
    batchBooks: "",
    // 显示模式：single（单本）、batch（批量）
    mode: "single",
    familyId: null,
    memberId: null,
  },

  onLoad() {
    // 页面加载时初始化家庭信息
    this.initFamily();
  },

  // 初始化家庭信息（复用 home 页的逻辑）
  async initFamily() {
    const families = await request("GET", "/v1/families");
    if (!families.length) {
      const fam = await request("POST", "/v1/families", { name: "我家" });
      this.setData({ familyId: fam.id });
    } else {
      this.setData({ familyId: families[0].id });
    }

    // 确保有成员
    const members = await request("GET", `/v1/families/${this.data.familyId}/members`);
    if (!members.length) {
      const m = await request("POST", `/v1/families/${this.data.familyId}/members`, { display_name: "我" });
      this.setData({ memberId: m.id });
    } else {
      this.setData({ memberId: members[0].id });
    }
  },

  // 确保家庭信息已初始化，如果没初始化过则等待
  async ensureFamilyInit() {
    if (!this.data.familyId || !this.data.memberId) {
      await this.initFamily();
    }
  },

  // 切换到单本模式
  switchToSingle() {
    this.setData({ mode: "single" });
  },

  // 切换到批量输入模式
  switchToBatch() {
    this.setData({ mode: "batch" });
  },

  onTitleInput(e) {
    this.setData({ title: e.detail.value });
  },

  onAuthorsInput(e) {
    this.setData({ authors: e.detail.value });
  },

  onPublisherInput(e) {
    this.setData({ publisher: e.detail.value });
  },

  // 添加单本书籍
  async addBook() {
    const title = this.data.title.trim();
    if (!title) {
      wx.showToast({
        title: '请输入书名',
        icon: 'none',
      });
      return;
    }

    try {
      this.setData({ loading: true });
      wx.showLoading({ title: '正在添加...' });

      // 1. 创建书籍
      const bookInfo = await request("POST", "/v1/books", {
        title: title,
        authors: this.data.authors,
        publisher: this.data.publisher || null,
        pub_date: null,
        isbn: null,
      });

      // 2. 确保家庭信息已初始化
      await this.ensureFamilyInit();

      // 3. 创建阅读记录
      if (this.data.familyId && this.data.memberId) {
        await request("POST", "/v1/readings", {
          family_id: this.data.familyId,
          member_id: this.data.memberId,
          book_meta_id: bookInfo.id,
          status: "reading",
          progress_type: "page",
          progress_value: 0,
        });
      }

      wx.hideLoading();
      wx.showToast({
        title: '添加成功',
        icon: 'success',
      });

      // 清空表单
      this.setData({ title: "", authors: "", publisher: "" });

      // 延迟返回，让用户看到成功提示
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      console.error('添加书籍失败:', e);
      wx.hideLoading();
      wx.showToast({
        title: '添加失败，请重试',
        icon: 'none',
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 批量输入书籍名字
  onBatchBooksInput(e) {
    this.setData({ batchBooks: e.detail.value });
  },

  // 批量添加书籍
  async addBatchBooks() {
    const batchBooks = this.data.batchBooks.trim();
    if (!batchBooks) {
      wx.showToast({
        title: '请输入书籍名字',
        icon: 'none',
      });
      return;
    }

    // 分割书籍名字（按换行或逗号分割）
    const bookTitles = batchBooks
      .split(/[\n,，]/)
      .map(title => title.trim())
      .filter(title => title);

    if (bookTitles.length === 0) {
      wx.showToast({
        title: '请输入有效的书籍名字',
        icon: 'none',
      });
      return;
    }

    try {
      this.setData({ loading: true });
      wx.showLoading({ title: '正在添加书籍...' });

      let successCount = 0;
      // 先确保家庭信息已初始化
      await this.ensureFamilyInit();

      for (const title of bookTitles) {
        try {
          // 1. 创建书籍
          const bookInfo = await request("POST", "/v1/books", {
            title: title,
            authors: "",
            publisher: null,
            pub_date: null,
            isbn: null,
          });

          // 2. 创建阅读记录
          if (this.data.familyId && this.data.memberId) {
            await request("POST", "/v1/readings", {
              family_id: this.data.familyId,
              member_id: this.data.memberId,
              book_meta_id: bookInfo.id,
              status: "reading",
              progress_type: "page",
              progress_value: 0,
            });
          }

          successCount++;
        } catch (e) {
          console.error(`添加书籍 ${title} 失败:`, e);
        }
      }

      wx.hideLoading();
      wx.showToast({
        title: `成功添加 ${successCount} 本书籍`,
        icon: 'success',
      });

      // 清空输入
      this.setData({ batchBooks: "" });

      // 延迟返回，让用户看到成功提示
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      console.error('批量添加失败:', e);
      wx.hideLoading();
      wx.showToast({
        title: '添加失败，请重试',
        icon: 'none',
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  navigateBack() {
    wx.navigateBack();
  },
});
