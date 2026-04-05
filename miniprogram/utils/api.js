const { BASE_URL } = require("./config");

function getToken() {
  return wx.getStorageSync("access_token") || "";
}

function request(method, path, data) {
  console.log('=== 开始网络请求 ===');
  console.log('请求URL:', `${BASE_URL}${path}`);
  console.log('请求方法:', method);
  console.log('请求数据:', data);
  console.log('请求头:', {
    "Content-Type": "application/json",
    Authorization: getToken() ? `Bearer ${getToken()}` : "",
  });

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${path}`,
      method,
      data,
      header: {
        "Content-Type": "application/json",
        Authorization: getToken() ? `Bearer ${getToken()}` : "",
      },
      success: (res) => {
        console.log('=== 网络请求响应 ===');
        console.log('响应状态码:', res.statusCode);
        console.log('响应数据:', res.data);

        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log('请求成功');
          return resolve(res.data);
        }
        console.log('请求失败，状态码:', res.statusCode);
        reject(res);
      },
      fail: (err) => {
        console.log('=== 网络请求失败 ===');
        console.error('请求失败:', err);
        reject(err);
      },
    });
  });
}

module.exports = {
  request,
};