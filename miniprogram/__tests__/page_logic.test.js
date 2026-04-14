/**
 * Page logic tests
 *
 * We use the actual `request()` from api.js as the API layer,
 * and mock wx.request to return controlled responses.
 * This way the tests exercise the real request wrapper (token injection,
 * URL construction, response extraction) alongside page business logic.
 */

const { request } = require('../utils/api');

// ---------- helpers ----------

function createPage(defaultData) {
  const data = { ...defaultData };
  return {
    get data() { return data; },
    set data(v) { Object.assign(data, v); },
    setData(obj) {
      for (const [key, value] of Object.entries(obj)) {
        if (key.includes('.')) {
          const parts = key.split('.');
          let target = data;
          for (let i = 0; i < parts.length - 1; i++) {
            if (!target[parts[i]]) target[parts[i]] = {};
            target = target[parts[i]];
          }
          target[parts[parts.length - 1]] = value;
        } else {
          data[key] = value;
        }
      }
    },
  };
}

// Mock wx.request to return { statusCode, data } — the real api.js
// extracts res.data and returns it, so test logic receives raw data.
function mockRequest(responses) {
  let i = 0;
  global.wx.request.mockImplementation(({ success, fail }) => {
    const r = responses[i++];
    if (r.error) return fail(r.error);
    success({ statusCode: r.statusCode || 200, data: r.data });
  });
}

// ---------- home page ----------

describe('home page logic', () => {
  let page;

  beforeEach(() => {
    page = createPage({ family: null, members: [], dash: null });

    page.bootstrap = async function () {
      const families = await request('GET', '/v1/families');
      if (!families.length) {
        const fam = await request('POST', '/v1/families', { name: '我家' });
        this.setData({ family: fam });
      } else {
        this.setData({ family: families[0] });
      }
      const members = await request('GET', `/v1/families/${this.data.family.id}/members`);
      if (!members.length) {
        await request('POST', `/v1/families/${this.data.family.id}/members`, { display_name: '我' });
      }
      await this.refresh();
    };

    page.refresh = async function () {
      const members = await request('GET', `/v1/families/${this.data.family.id}/members`);
      const dash = await request('GET', `/v1/families/${this.data.family.id}/dashboard`);
      this.setData({ members, dash });
    };

    page.onShow = async function () {
      const token = global.wx.getStorageSync('access_token');
      if (!token) return global.wx.reLaunch({ url: '/pages/login/index' });
      await this.bootstrap();
    };

    page.logout = function () {
      global.wx.removeStorageSync('access_token');
      global.wx.removeStorageSync('user');
      global.wx.reLaunch({ url: '/pages/login/index' });
    };
  });

  describe('logout()', () => {
    it('clears storage and redirects to login', () => {
      page.logout();
      expect(global.wx.removeStorageSync).toHaveBeenCalledWith('access_token');
      expect(global.wx.removeStorageSync).toHaveBeenCalledWith('user');
      expect(global.wx.reLaunch).toHaveBeenCalledWith({ url: '/pages/login/index' });
    });
  });
});

// ---------- login page ----------

describe('login page logic', () => {
  let page;

  beforeEach(() => {
    page = createPage({ loading: false });

    page.onLoad = async function () {
      const token = global.wx.getStorageSync('access_token');
      if (token) {
        global.wx.reLaunch({ url: '/pages/home/index' });
      }
    };

    page.devLogin = async function () {
      try {
        this.setData({ loading: true });
        const res = await request('POST', '/v1/auth/dev/login', { openid: 'dev-user-1' });
        global.wx.setStorageSync('access_token', res.access_token);
        global.wx.setStorageSync('user', res.user);
        global.wx.showToast({ title: '开发测试登录成功' });
        global.wx.reLaunch({ url: '/pages/home/index' });
      } catch (e) {
        global.wx.showModal({
          title: '登录失败',
          content: (e && e.data && e.data.detail) || '请检查后端是否启动',
          showCancel: false,
        });
      } finally {
        this.setData({ loading: false });
      }
    };
  });

  describe('onLoad()', () => {
    it('redirects to home when token exists', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      await page.onLoad();
      expect(global.wx.reLaunch).toHaveBeenCalledWith({ url: '/pages/home/index' });
    });

    it('stays on login page when no token', async () => {
      global.wx.getStorageSync.mockReturnValue('');
      await page.onLoad();
      expect(global.wx.reLaunch).not.toHaveBeenCalled();
    });
  });

  describe('devLogin()', () => {
    it('sends correct openid to dev login endpoint', async () => {
      mockRequest([{ data: { access_token: 'u:1', user: { id: 1 } } }]);

      await page.devLogin();

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          url: expect.stringContaining('/v1/auth/dev/login'),
        })
      );
    });

    it('saves token and redirects on success', async () => {
      mockRequest([{ data: { access_token: 'u:1', user: { id: 1 } } }]);

      await page.devLogin();

      expect(global.wx.setStorageSync).toHaveBeenCalledWith('access_token', 'u:1');
      expect(global.wx.reLaunch).toHaveBeenCalledWith({ url: '/pages/home/index' });
    });

    it('shows error modal on failure', async () => {
      mockRequest([{ error: new Error('connection refused') }]);

      await page.devLogin();

      expect(global.wx.showModal).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '登录失败',
          showCancel: false,
        })
      );
    });
  });
});

// ---------- scan_add page ----------

describe('scan_add page logic', () => {
  let page;

  beforeEach(() => {
    page = createPage({
      title: '', authors: '', publisher: '',
      loading: false, batchBooks: '', mode: 'single',
      familyId: null, memberId: null,
    });

    page.ensureFamilyInit = async function () {
      if (!this.data.familyId || !this.data.memberId) {
        const families = await request('GET', '/v1/families');
        if (!families.length) {
          const fam = await request('POST', '/v1/families', { name: '我家' });
          this.setData({ familyId: fam.id });
        } else {
          this.setData({ familyId: families[0].id });
        }
        const members = await request('GET', `/v1/families/${this.data.familyId}/members`);
        if (!members.length) {
          const m = await request('POST', `/v1/families/${this.data.familyId}/members`, { display_name: '我' });
          this.setData({ memberId: m.id });
        } else {
          this.setData({ memberId: members[0].id });
        }
      }
    };

    page.addBook = async function () {
      const title = this.data.title.trim();
      if (!title) {
        global.wx.showToast({ title: '请输入书名', icon: 'none' });
        return;
      }
      try {
        this.setData({ loading: true });
        const bookInfo = await request('POST', '/v1/books', {
          title, authors: this.data.authors, publisher: this.data.publisher || null,
          pub_date: null, isbn: null,
        });
        await this.ensureFamilyInit();
        if (this.data.familyId && this.data.memberId) {
          await request('POST', '/v1/readings', {
            family_id: this.data.familyId, member_id: this.data.memberId,
            book_meta_id: bookInfo.id, status: 'reading',
            progress_type: 'page', progress_value: 0,
          });
        }
        global.wx.showToast({ title: '添加成功', icon: 'success' });
        this.setData({ title: '', authors: '', publisher: '' });
      } catch (e) {
        global.wx.showToast({ title: '添加失败，请重试', icon: 'none' });
      } finally {
        this.setData({ loading: false });
      }
    };

    page.addBatchBooks = async function () {
      const batchBooks = this.data.batchBooks.trim();
      if (!batchBooks) {
        global.wx.showToast({ title: '请输入书籍名字', icon: 'none' });
        return;
      }
      const bookTitles = batchBooks.split(/[\n,，]/).map(t => t.trim()).filter(t => t);
      try {
        this.setData({ loading: true });
        await this.ensureFamilyInit();
        let successCount = 0;
        for (const title of bookTitles) {
          try {
            const bookInfo = await request('POST', '/v1/books', {
              title, authors: '', publisher: null, pub_date: null, isbn: null,
            });
            if (this.data.familyId && this.data.memberId) {
              await request('POST', '/v1/readings', {
                family_id: this.data.familyId, member_id: this.data.memberId,
                book_meta_id: bookInfo.id, status: 'reading',
                progress_type: 'page', progress_value: 0,
              });
            }
            successCount++;
          } catch (e) { /* continue */ }
        }
        global.wx.showToast({ title: `成功添加 ${successCount} 本书籍`, icon: 'success' });
        this.setData({ batchBooks: '' });
      } catch (e) {
        global.wx.showToast({ title: '添加失败，请重试', icon: 'none' });
      } finally {
        this.setData({ loading: false });
      }
    };
  });

  describe('addBook()', () => {
    it('rejects empty title', async () => {
      page.setData({ title: '' });
      await page.addBook();
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '请输入书名', icon: 'none' })
      );
    });

    it('creates book and reading record with valid title', async () => {
      page.setData({
        title: '测试书籍', authors: '作者', publisher: '出版社',
        familyId: 1, memberId: 2,
      });
      mockRequest([
        { data: { id: 100, title: '测试书籍' } },
        { data: { id: 200 } },
      ]);

      await page.addBook();

      expect(global.wx.request).toHaveBeenCalledTimes(2);
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '添加成功', icon: 'success' })
      );
    });
  });

  describe('addBatchBooks()', () => {
    it('rejects empty input', async () => {
      page.setData({ batchBooks: '' });
      await page.addBatchBooks();
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '请输入书籍名字', icon: 'none' })
      );
    });

    it('parses titles separated by newlines and commas', async () => {
      page.setData({ batchBooks: '书A\n书B,书C\n书D', familyId: 1, memberId: 2 });
      const responses = [];
      for (let i = 0; i < 4; i++) {
        responses.push({ data: { id: 100 + i } });
        responses.push({ data: { id: 200 + i } });
      }
      mockRequest(responses);

      await page.addBatchBooks();

      expect(global.wx.request).toHaveBeenCalledTimes(8);
    });

    it('continues adding remaining books when one fails', async () => {
      page.setData({ batchBooks: '好书\n坏书', familyId: 1, memberId: 2 });
      mockRequest([
        { error: new Error('server error') },
        { data: { id: 200 } },
        { data: { id: 300 } },
      ]);

      await page.addBatchBooks();

      expect(global.wx.request).toHaveBeenCalledTimes(3);
    });
  });
});

// ---------- reading_list page ----------

describe('reading_list page logic', () => {
  let page;

  beforeEach(() => {
    page = createPage({
      readingList: [], loading: true, error: false, familyId: null,
    });

    page.getReadingList = async function () {
      try {
        this.setData({ loading: true, error: false });
        const familyId = this.data.familyId;
        if (!familyId) throw new Error('家庭ID不存在');
        const readings = await request('GET', `/v1/families/${familyId}/readings`);
        const readingList = readings.map(reading => {
          const book = reading.book || {};
          return {
            id: reading.id,
            book: {
              title: book.title || '未知书籍',
              author: (book.authors || []).join(', ') || '未知作者',
              cover: book.cover_url || null,
            },
            status: reading.status,
            progress: reading.progress_value,
            updatedAt: reading.updated_at,
          };
        });
        this.setData({ readingList, loading: false });
      } catch (e) {
        this.setData({ error: true, loading: false });
      }
    };

    page.deleteReading = async function (e) {
      const readingId = e.currentTarget.dataset.id;
      const item = this.data.readingList.find(r => r.id === readingId);
      global.wx.showModal({
        title: '确认删除',
        content: `确定要删除"${item ? item.book.title : '该记录'}"吗？`,
      });
      try {
        await request('DELETE', `/v1/readings/${readingId}`);
        this.setData({
          readingList: this.data.readingList.filter(r => r.id !== readingId),
        });
        global.wx.showToast({ title: '已删除', icon: 'success' });
      } catch (e) {
        global.wx.showToast({ title: '删除失败，请重试', icon: 'none' });
      }
    };

    page.bootstrap = async function () {
      const families = await request('GET', '/v1/families');
      if (!families.length) {
        const fam = await request('POST', '/v1/families', { name: '我家' });
        this.setData({ familyId: fam.id });
      } else {
        this.setData({ familyId: families[0].id });
      }
      await this.getReadingList();
    };
  });

  describe('getReadingList()', () => {
    it('fetches readings and maps book data correctly', async () => {
      page.setData({ familyId: 1 });
      mockRequest([{
        data: [{
          id: 1,
          book: { title: '西游记', authors: ['吴承恩'], cover_url: 'http://img.jpg' },
          status: 'reading', progress_value: 50, updated_at: '2024-01-01',
        }],
      }]);

      await page.getReadingList();

      expect(page.data.readingList).toHaveLength(1);
      expect(page.data.readingList[0].book.title).toBe('西游记');
      expect(page.data.readingList[0].book.author).toBe('吴承恩');
      expect(page.data.readingList[0].progress).toBe(50);
    });

    it('handles empty reading list', async () => {
      page.setData({ familyId: 1 });
      mockRequest([{ data: [] }]);

      await page.getReadingList();

      expect(page.data.readingList).toEqual([]);
      expect(page.data.loading).toBe(false);
    });
  });

  describe('deleteReading()', () => {
    it('deletes reading record after confirmation', async () => {
      page.setData({
        familyId: 1,
        readingList: [
          { id: 1, book: { title: '西游记' }, status: 'reading', progress: 50 },
          { id: 2, book: { title: '水浒传' }, status: 'finished', progress: 100 },
        ],
      });
      mockRequest([{ data: {} }]);

      await page.deleteReading({ currentTarget: { dataset: { id: 1 } } });

      expect(page.data.readingList).toHaveLength(1);
      expect(page.data.readingList[0].id).toBe(2);
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '已删除', icon: 'success' })
      );
    });
  });

  describe('bootstrap()', () => {
    it('creates default family when none exist', async () => {
      mockRequest([
        { data: [] },
        { data: { id: 1, name: '我家' } },
        { data: [] },
      ]);

      await page.bootstrap();

      expect(page.data.familyId).toBe(1);
    });
  });
});

// ---------- reading_detail page ----------

describe('reading_detail page logic', () => {
  const STATUS_LABELS = {
    wishlist: '想读', reading: '阅读中', finished: '已读完',
    paused: '暂停', rereading: '重读',
  };
  let page;

  beforeEach(() => {
    page = createPage({
      reading: null, loading: true, error: false,
      progress: 0, readingId: null, familyId: null,
      statusLabels: STATUS_LABELS,
    });

    page.getReadingDetail = async function (id) {
      try {
        this.setData({ loading: true, error: false });
        const reading = await request('GET', `/v1/readings/${id}`);
        const book = reading.book || {};
        const families = await request('GET', '/v1/families');
        if (families && families.length > 0) {
          this.setData({ familyId: families[0].id });
        }
        this.setData({
          reading: {
            id: reading.id,
            book: {
              title: book.title || '未知书籍',
              author: (book.authors || []).join(', ') || '未知作者',
              cover: book.cover_url || null,
              isbn: book.isbn13 || '',
              pages: null,
            },
            status: reading.status,
            progress: reading.progress_value,
            startDate: reading.started_on || '未知',
            updatedAt: reading.updated_at,
            note: reading.note || '',
          },
          progress: reading.progress_value,
          loading: false,
        });
      } catch (e) {
        this.setData({ error: true, loading: false });
        global.wx.showToast({ title: '获取阅读详情失败', icon: 'none' });
      }
    };

    page.saveProgress = async function () {
      const readingId = this.data.readingId;
      if (!readingId) {
        global.wx.showToast({ title: '阅读记录不存在', icon: 'none' });
        return;
      }
      try {
        global.wx.showLoading({ title: '保存中...' });
        await request('PATCH', `/v1/readings/${readingId}`, { progress_value: this.data.progress });
        global.wx.hideLoading();
        global.wx.showToast({ title: '保存成功', icon: 'success' });
      } catch (e) {
        global.wx.hideLoading();
        global.wx.showToast({ title: '保存失败，请重试', icon: 'none' });
      }
    };

    page.changeStatus = async function (e) {
      const newStatus = e.currentTarget.dataset.status;
      const readingId = this.data.readingId;
      if (!readingId) return;
      try {
        global.wx.showLoading({ title: '更新中...' });
        await request('PATCH', `/v1/readings/${readingId}`, { status: newStatus });
        this.setData({ 'reading.status': newStatus });
        global.wx.hideLoading();
        global.wx.showToast({
          title: `状态已更新为"${STATUS_LABELS[newStatus] || newStatus}"`,
          icon: 'success',
        });
      } catch (e) {
        global.wx.hideLoading();
        global.wx.showToast({ title: '更新失败，请重试', icon: 'none' });
      }
    };
  });

  describe('getReadingDetail()', () => {
    it('fetches reading and maps book data', async () => {
      mockRequest([
        {
          data: {
            id: 1, book: { title: '红楼梦', authors: ['曹雪芹'], cover_url: null, isbn13: null },
            status: 'reading', progress_value: 30, started_on: '2024-01-01',
            updated_at: '2024-01-15', note: '',
          },
        },
        { data: [{ id: 1, name: '我家' }] },
      ]);

      await page.getReadingDetail(1);

      expect(page.data.reading.book.title).toBe('红楼梦');
      expect(page.data.reading.status).toBe('reading');
      expect(page.data.progress).toBe(30);
      expect(page.data.loading).toBe(false);
    });

    it('shows error toast on failure', async () => {
      mockRequest([{ error: new Error('network error') }]);

      await page.getReadingDetail(1);

      expect(page.data.loading).toBe(false);
      expect(page.data.error).toBe(true);
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '获取阅读详情失败', icon: 'none' })
      );
    });
  });

  describe('saveProgress()', () => {
    it('sends PATCH request with progress_value', async () => {
      page.setData({ readingId: 5, progress: 75 });
      mockRequest([{ data: {} }]);

      await page.saveProgress();

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'PATCH',
          url: expect.stringContaining('/v1/readings/5'),
          data: { progress_value: 75 },
        })
      );
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '保存成功', icon: 'success' })
      );
    });

    it('shows error when readingId is null', async () => {
      page.setData({ readingId: null });
      await page.saveProgress();
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '阅读记录不存在', icon: 'none' })
      );
    });
  });

  describe('changeStatus()', () => {
    it('sends PATCH with new status', async () => {
      page.setData({ readingId: 5, reading: { status: 'reading' } });
      mockRequest([{ data: {} }]);

      await page.changeStatus({ currentTarget: { dataset: { status: 'finished' } } });

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({ method: 'PATCH', data: { status: 'finished' } })
      );
      expect(page.data.reading.status).toBe('finished');
    });

    it('shows translated status label in toast', async () => {
      page.setData({ readingId: 5, reading: { status: 'reading' } });
      mockRequest([{ data: {} }]);

      await page.changeStatus({ currentTarget: { dataset: { status: 'finished' } } });

      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '状态已更新为"已读完"', icon: 'success' })
      );
    });
  });
});

// ---------- settings page ----------

describe('settings page logic', () => {
  let page;

  beforeEach(() => {
    page = createPage({
      family: null, members: [], loading: true, error: false,
      editingFamilyName: false, familyName: '', newMemberName: '',
      showAddMember: false,
    });

    page.loadFamily = async function () {
      try {
        this.setData({ loading: true, error: false });
        const families = await request('GET', '/v1/families');
        if (!families.length) {
          const fam = await request('POST', '/v1/families', { name: '我家' });
          this.setData({ family: fam, familyName: fam.name });
        } else {
          this.setData({ family: families[0], familyName: families[0].name });
        }
        await this.loadMembers();
      } catch (e) {
        this.setData({ error: true, loading: false });
      }
    };

    page.loadMembers = async function () {
      const familyId = this.data.family.id;
      const members = await request('GET', `/v1/families/${familyId}/members`);
      this.setData({ members, loading: false });
    };

    page.addMember = async function () {
      const name = this.data.newMemberName.trim();
      if (!name) {
        global.wx.showToast({ title: '请输入成员名称', icon: 'none' });
        return;
      }
      try {
        const familyId = this.data.family.id;
        const member = await request('POST', `/v1/families/${familyId}/members`, { display_name: name });
        this.setData({
          members: [...this.data.members, member],
          showAddMember: false, newMemberName: '',
        });
        global.wx.showToast({ title: '添加成功', icon: 'success' });
      } catch (e) {
        global.wx.showToast({ title: '添加失败，请重试', icon: 'none' });
      }
    };

    page.goBack = function () {
      global.wx.navigateBack();
    };
  });

  describe('loadFamily()', () => {
    it('creates default family when none exist', async () => {
      mockRequest([
        { data: [] },
        { data: { id: 1, name: '我家' } },
        { data: [{ id: 1, display_name: '我' }] },
      ]);

      await page.loadFamily();

      expect(page.data.family).toEqual({ id: 1, name: '我家' });
    });
  });

  describe('addMember()', () => {
    it('rejects empty name', async () => {
      page.setData({ newMemberName: '' });
      await page.addMember();
      expect(global.wx.showToast).toHaveBeenCalledWith(
        expect.objectContaining({ title: '请输入成员名称', icon: 'none' })
      );
    });

    it('creates member and updates list', async () => {
      page.setData({
        family: { id: 1 }, newMemberName: '爸爸',
        members: [{ id: 1, display_name: '我' }],
      });
      mockRequest([{ data: { id: 2, display_name: '爸爸' } }]);

      await page.addMember();

      expect(page.data.members).toHaveLength(2);
      expect(page.data.members[1].display_name).toBe('爸爸');
      expect(page.data.showAddMember).toBe(false);
    });
  });

  describe('goBack()', () => {
    it('calls navigateBack', () => {
      page.goBack();
      expect(global.wx.navigateBack).toHaveBeenCalled();
    });
  });
});
