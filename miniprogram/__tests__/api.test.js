// api.js uses global.wx, so we test via global.wx
const { request } = require('../utils/api');
const { BASE_URL } = require('../utils/config');

describe('api.js request layer', () => {
  describe('request()', () => {
    it('constructs correct URL with BASE_URL', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 200, data: { ok: true } });
      });

      await request('GET', '/v1/health');

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          url: `${BASE_URL}/v1/health`,
          method: 'GET',
        })
      );
    });

    it('sends Bearer token when access_token exists', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 200, data: {} });
      });

      await request('GET', '/v1/families');

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          header: expect.objectContaining({
            Authorization: 'Bearer u:test-123',
          }),
        })
      );
    });

    it('sends empty Authorization when no token', async () => {
      global.wx.getStorageSync.mockReturnValue('');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 200, data: {} });
      });

      await request('GET', '/v1/health');

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          header: expect.objectContaining({
            Authorization: '',
          }),
        })
      );
    });

    it('resolves with res.data on 2xx status', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 200, data: { id: 1, name: 'test' } });
      });

      const result = await request('GET', '/v1/families/1');

      expect(result).toEqual({ id: 1, name: 'test' });
    });

    it('rejects on non-2xx status', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 401, data: { detail: 'unauthorized' } });
      });

      await expect(request('GET', '/v1/families')).rejects.toMatchObject({
        statusCode: 401,
      });
    });

    it('rejects on network failure', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ fail }) => {
        fail(new Error('network error'));
      });

      await expect(request('POST', '/v1/books', { title: 'test' })).rejects.toThrow('network error');
    });

    it('sends request body as data for POST', async () => {
      global.wx.getStorageSync.mockReturnValue('u:test-123');
      global.wx.request.mockImplementation(({ success }) => {
        success({ statusCode: 201, data: { id: 1 } });
      });

      const body = { title: '测试书籍', authors: '作者' };
      await request('POST', '/v1/books', body);

      expect(global.wx.request).toHaveBeenCalledWith(
        expect.objectContaining({
          data: body,
          method: 'POST',
        })
      );
    });
  });
});
